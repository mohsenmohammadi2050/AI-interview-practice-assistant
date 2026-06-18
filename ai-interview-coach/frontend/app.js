import {
  evaluateAnswer,
  getNextQuestion,
  getPublicConfig,
  saveSession,
  startInterview,
  transcribeAudio,
} from "./api.js";

const elements = {
  providerInfo: document.querySelector("#providerInfo"),
  jobAnnouncement: document.querySelector("#jobAnnouncement"),
  jobFile: document.querySelector("#jobFile"),
  candidateProfile: document.querySelector("#candidateProfile"),
  candidateFile: document.querySelector("#candidateFile"),
  agentInstructions: document.querySelector("#agentInstructions"),
  instructionFile: document.querySelector("#instructionFile"),
  languageMode: document.querySelector("#languageMode"),
  startInterviewBtn: document.querySelector("#startInterviewBtn"),
  setupError: document.querySelector("#setupError"),
  currentQuestion: document.querySelector("#currentQuestion"),
  saveSessionBtn: document.querySelector("#saveSessionBtn"),
  startRecordingBtn: document.querySelector("#startRecordingBtn"),
  stopRecordingBtn: document.querySelector("#stopRecordingBtn"),
  transcribeBtn: document.querySelector("#transcribeBtn"),
  recordingStatus: document.querySelector("#recordingStatus"),
  recordingError: document.querySelector("#recordingError"),
  audioPreview: document.querySelector("#audioPreview"),
  answerTranscript: document.querySelector("#answerTranscript"),
  submitAnswerBtn: document.querySelector("#submitAnswerBtn"),
  retryQuestionBtn: document.querySelector("#retryQuestionBtn"),
  nextQuestionBtn: document.querySelector("#nextQuestionBtn"),
  interviewError: document.querySelector("#interviewError"),
  feedbackContent: document.querySelector("#feedbackContent"),
  sessionHistory: document.querySelector("#sessionHistory"),
};

let session = null;
let currentQuestion = null;
let mediaRecorder = null;
let recordedChunks = [];
let recordedBlob = null;
let pendingTurn = null;

function setError(target, message = "") {
  target.textContent = message;
}

function setBusy(button, busy, text) {
  button.disabled = busy;
  if (text) button.textContent = text;
}

function setupPayload() {
  return {
    job_announcement: elements.jobAnnouncement.value.trim(),
    candidate_profile: elements.candidateProfile.value.trim(),
    agent_instructions: elements.agentInstructions.value.trim(),
    language_mode: elements.languageMode.value,
  };
}

function renderQuestion(question) {
  currentQuestion = question;
  pendingTurn = null;
  elements.currentQuestion.innerHTML = `
    <div class="question-meta">
      <span>${question.category}</span>
      <span>${question.difficulty}</span>
      <span>${question.language}</span>
    </div>
    <p>${escapeHtml(question.question)}</p>
  `;
  elements.submitAnswerBtn.disabled = false;
  elements.retryQuestionBtn.disabled = true;
  elements.nextQuestionBtn.disabled = true;
  elements.answerTranscript.value = "";
}

function renderFeedback(evaluation) {
  const scores = evaluation.scores || {};
  elements.feedbackContent.className = "";
  elements.feedbackContent.innerHTML = `
    <div class="score">Overall score: <strong>${evaluation.overall_score}/5</strong></div>
    <div class="score-grid">
      ${Object.entries(scores)
        .map(([key, value]) => `<span>${formatLabel(key)}: <strong>${value}/5</strong></span>`)
        .join("")}
    </div>
    ${renderList("Strengths", evaluation.strengths)}
    ${renderList("Weaknesses", evaluation.weaknesses)}
    <h3>Improved answer</h3>
    <p>${escapeHtml(evaluation.improved_answer || "")}</p>
    ${renderList("Speaking tips", evaluation.speaking_tips)}
    <h3>Next focus</h3>
    <p>${escapeHtml(evaluation.next_focus || "")}</p>
    <p><strong>Retry recommendation:</strong> ${evaluation.should_retry_question ? "Retry this question." : "Continue to the next question."}</p>
  `;
}

function renderHistory() {
  if (!session || !session.turns.length) {
    elements.sessionHistory.className = "empty";
    elements.sessionHistory.textContent = "No answers yet.";
    return;
  }
  elements.sessionHistory.className = "";
  elements.sessionHistory.innerHTML = session.turns
    .map((turn, index) => {
      const score = turn.evaluation?.overall_score ? `${turn.evaluation.overall_score}/5` : "not scored";
      return `
        <article class="history-item">
          <div class="history-title">Question ${index + 1} <span>${score}</span></div>
          <p><strong>Q:</strong> ${escapeHtml(turn.question || "")}</p>
          <p><strong>A:</strong> ${escapeHtml(turn.answer_transcript || "")}</p>
          <p><strong>Focus:</strong> ${escapeHtml(turn.evaluation?.next_focus || "")}</p>
        </article>
      `;
    })
    .join("");
}

function renderList(title, items = []) {
  if (!items.length) return "";
  return `
    <h3>${title}</h3>
    <ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
  `;
}

function formatLabel(value) {
  return value.replaceAll("_", " ");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadConfig() {
  try {
    const config = await getPublicConfig();
    elements.providerInfo.textContent = `${config.llm_provider}: ${config.llm_model} | STT: ${config.transcription_model}`;
  } catch (error) {
    elements.providerInfo.textContent = "Backend unavailable";
  }
}

function buildTurn(question, answerTranscript, evaluation) {
  return {
    question: question?.question || "",
    question_metadata: question || {},
    answer_transcript: answerTranscript,
    evaluation,
    created_at: new Date().toISOString(),
  };
}

async function commitPendingTurn() {
  if (!session || !pendingTurn) return;
  session.turns.push(pendingTurn);
  pendingTurn = null;
  session = await saveSession({ session });
  renderHistory();
}

function resetRecorderForRetry() {
  recordedChunks = [];
  recordedBlob = null;
  elements.audioPreview.hidden = true;
  elements.audioPreview.removeAttribute("src");
  elements.transcribeBtn.disabled = true;
  elements.recordingStatus.textContent = "Recording not started.";
}

async function loadTextFileIntoTextarea(event, textarea, label) {
  const file = event.target.files?.[0];
  if (!file) return;
  const lowerName = file.name.toLowerCase();
  if (!lowerName.endsWith(".txt") && !lowerName.endsWith(".md")) {
    setError(elements.setupError, `Only .txt and .md files are supported for ${label}.`);
    return;
  }
  try {
    textarea.value = await file.text();
    setError(elements.setupError);
  } catch (error) {
    setError(elements.setupError, `Could not read ${label} file: ${error.message}`);
  }
}

elements.jobFile.addEventListener("change", (event) => {
  loadTextFileIntoTextarea(event, elements.jobAnnouncement, "job announcement");
});

elements.candidateFile.addEventListener("change", (event) => {
  loadTextFileIntoTextarea(event, elements.candidateProfile, "candidate profile");
});

elements.instructionFile.addEventListener("change", (event) => {
  loadTextFileIntoTextarea(event, elements.agentInstructions, "agent instructions");
});

elements.startInterviewBtn.addEventListener("click", async () => {
  setError(elements.setupError);
  setError(elements.interviewError);
  setBusy(elements.startInterviewBtn, true, "Starting...");
  try {
    const result = await startInterview(setupPayload());
    session = result.session;
    pendingTurn = null;
    renderQuestion(result.question);
    renderHistory();
    elements.saveSessionBtn.disabled = false;
    elements.startRecordingBtn.disabled = false;
  } catch (error) {
    setError(elements.setupError, error.message);
  } finally {
    setBusy(elements.startInterviewBtn, false, "Start interview");
  }
});

elements.startRecordingBtn.addEventListener("click", async () => {
  setError(elements.recordingError);
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recordedChunks = [];
    recordedBlob = null;
    mediaRecorder = new MediaRecorder(stream, { mimeType: preferredMimeType() });
    mediaRecorder.addEventListener("dataavailable", (event) => {
      if (event.data.size > 0) recordedChunks.push(event.data);
    });
    mediaRecorder.addEventListener("stop", () => {
      recordedBlob = new Blob(recordedChunks, { type: mediaRecorder.mimeType || "audio/webm" });
      elements.audioPreview.src = URL.createObjectURL(recordedBlob);
      elements.audioPreview.hidden = false;
      elements.transcribeBtn.disabled = false;
      stream.getTracks().forEach((track) => track.stop());
    });
    mediaRecorder.start();
    elements.recordingStatus.textContent = "Recording...";
    elements.startRecordingBtn.disabled = true;
    elements.stopRecordingBtn.disabled = false;
  } catch (error) {
    setError(elements.recordingError, `Microphone unavailable: ${error.message}`);
  }
});

elements.stopRecordingBtn.addEventListener("click", () => {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
    elements.recordingStatus.textContent = "Recording stopped. Ready to transcribe.";
    elements.stopRecordingBtn.disabled = true;
    elements.startRecordingBtn.disabled = false;
  }
});

elements.transcribeBtn.addEventListener("click", async () => {
  if (!recordedBlob) return;
  setError(elements.recordingError);
  setBusy(elements.transcribeBtn, true, "Transcribing...");
  try {
    const extension = recordedBlob.type.includes("mp4") ? "mp4" : "webm";
    const audioFile = new File([recordedBlob], `answer.${extension}`, { type: recordedBlob.type });
    const result = await transcribeAudio(audioFile);
    elements.answerTranscript.value = result.transcript || "";
    elements.recordingStatus.textContent = "Transcript ready. Edit it before submitting.";
  } catch (error) {
    setError(elements.recordingError, `${error.message} You can type the answer manually below.`);
  } finally {
    setBusy(elements.transcribeBtn, false, "Upload / transcribe");
  }
});

elements.submitAnswerBtn.addEventListener("click", async () => {
  if (!session || !currentQuestion) return;
  setError(elements.interviewError);
  setBusy(elements.submitAnswerBtn, true, "Evaluating...");
  try {
    const result = await evaluateAnswer({
      session,
      question: currentQuestion,
      answer_transcript: elements.answerTranscript.value.trim(),
    });
    session = result.session;
    pendingTurn = buildTurn(currentQuestion, elements.answerTranscript.value.trim(), result.evaluation);
    renderFeedback(result.evaluation);
    elements.retryQuestionBtn.disabled = false;
    elements.nextQuestionBtn.disabled = false;
  } catch (error) {
    setError(elements.interviewError, error.message);
  } finally {
    setBusy(elements.submitAnswerBtn, false, "Submit answer");
  }
});

elements.retryQuestionBtn.addEventListener("click", () => {
  if (!session || !currentQuestion) return;
  setError(elements.interviewError);
  elements.answerTranscript.value = "";
  pendingTurn = null;
  resetRecorderForRetry();
  elements.feedbackContent.className = "empty";
  elements.feedbackContent.textContent = "Retry this question, then submit your new answer.";
  elements.submitAnswerBtn.disabled = false;
  elements.retryQuestionBtn.disabled = true;
  elements.nextQuestionBtn.disabled = true;
});

elements.nextQuestionBtn.addEventListener("click", async () => {
  if (!session) return;
  setError(elements.interviewError);
  setBusy(elements.nextQuestionBtn, true, "Loading...");
  let loaded = false;
  try {
    await commitPendingTurn();
    const result = await getNextQuestion({ session });
    renderQuestion(result.question);
    resetRecorderForRetry();
    loaded = true;
  } catch (error) {
    setError(elements.interviewError, error.message);
  } finally {
    setBusy(elements.nextQuestionBtn, false, "Next question");
    if (loaded) elements.nextQuestionBtn.disabled = true;
  }
});

elements.saveSessionBtn.addEventListener("click", async () => {
  if (!session) return;
  setError(elements.interviewError);
  setBusy(elements.saveSessionBtn, true, "Saving...");
  try {
    await commitPendingTurn();
    session = await saveSession({ session });
  } catch (error) {
    setError(elements.interviewError, error.message);
  } finally {
    setBusy(elements.saveSessionBtn, false, "Save session");
  }
});

function preferredMimeType() {
  const types = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
  return types.find((type) => MediaRecorder.isTypeSupported(type)) || "";
}

loadConfig();
