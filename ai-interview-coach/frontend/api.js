const API_BASE_URL = "http://127.0.0.1:8000";

async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail = data?.detail || response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

export function getPublicConfig() {
  return requestJson("/config/public");
}

export function startInterview(payload) {
  return requestJson("/interview/start", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getNextQuestion(payload) {
  return requestJson("/interview/next-question", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function evaluateAnswer(payload) {
  return requestJson("/interview/evaluate-answer", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function transcribeAudio(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE_URL}/transcription/transcribe`, {
    method: "POST",
    body: formData,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data?.detail || response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

export function saveSession(payload) {
  return requestJson("/sessions/save", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listSessions() {
  return requestJson("/sessions");
}

export function getSession(sessionId) {
  return requestJson(`/sessions/${encodeURIComponent(sessionId)}`);
}
