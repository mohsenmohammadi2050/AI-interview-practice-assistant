# AI Interview Coach - Voice-Based AI Interview Practice App

AI Interview Coach is a local two-agent interview practice app. It simulates a realistic hiring manager, lets a candidate answer by voice, transcribes the answer with Groq Whisper, and uses an OpenRouter-hosted LLM to give structured coaching feedback.

The goal is practical interview preparation: realistic questions, editable transcripts, honest feedback, improved answers, and the option to retry weak answers before moving on.

## Highlights

- Realistic hiring-manager question generation based on a job announcement, candidate profile, and custom agent instructions.
- Spoken-answer workflow with browser audio recording and file-based speech-to-text.
- Groq speech-to-text using `whisper-large-v3`.
- OpenRouter LLM support through an OpenAI-compatible chat completions client.
- Provider-agnostic backend: OpenRouter, OpenAI, Groq, or other OpenAI-compatible providers can be configured from `.env`.
- Plain HTML, CSS, and JavaScript frontend. No React, Vite, npm, Docker, database, LangChain, or LangGraph.
- Local JSON session storage.
- Retry flow: if feedback recommends retrying a question, the candidate can answer the same question again before saving the attempt.
- Template Markdown files for job announcements, candidate profiles, and custom agent behavior instructions.

## Agent Design

The app uses two focused AI agents instead of a complicated orchestration framework.

### 1. Hiring Manager Agent

The Hiring Manager Agent generates one realistic interview question at a time. It uses:

- job announcement
- candidate profile/CV
- custom agent instructions
- previous questions and answers
- previous coach feedback
- selected language mode

It adapts the interview flow by asking practical technical, behavioral, motivation, project, role-fit, communication, and follow-up questions. It does not evaluate the candidate or give feedback.

### 2. Interview Coach Agent

The Interview Coach Agent evaluates the candidate's submitted transcript. It returns structured feedback with:

- overall score
- category scores
- strengths
- weaknesses
- improved answer
- speaking tips
- next focus
- retry recommendation

The coach is honest but supportive. It focuses on realistic spoken interview performance, not perfect written answers.

### Custom Agent Instructions

Users can upload or paste extra instructions from a human hiring manager, recruiter, mentor, or their own notes. These instructions are passed to both agents:

- the Hiring Manager Agent uses them to shape question style and priorities
- the Interview Coach Agent uses them to shape evaluation and feedback

The base prompts define the permanent rules of each agent. Custom instructions make each interview session more specific and realistic.

## Tech Stack

- Backend: FastAPI, Pydantic, httpx
- Frontend: HTML, CSS, JavaScript
- LLM provider: OpenRouter by default
- Speech-to-text provider: Groq by default
- Storage: local JSON files under `data/`

## Project Structure

```text
ai-interview-coach/
  backend/
    run_backend.py
    app/
      agents/
      llm/
      routes/
      services/
      config.py
      main.py
      models.py
      storage.py
  frontend/
    index.html
    styles.css
    app.js
    api.js
  prompts/
    hiring_manager_prompt.md
    interview_coach_prompt.md
  templates/
    candidate_profile_template.md
    job_announcement_template.md
    agent_instructions_template.md
    evaluation_rubric_template.md
    language_settings_template.md
  .env.example
  requirements.txt
  README.md
```

## Setup

Create and activate a virtual environment:

```powershell
cd F:\Hiring_manager\ai-interview-coach
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and add your API keys.

## Environment Variables

### OpenRouter LLM

```env
LLM_PROVIDER=openrouter
LLM_API_KEY=your_openrouter_api_key_here
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=nex-agi/nex-n2-pro:free
LLM_MAX_RETRIES=3
```

`LLM_MODEL` must be explicit. The app does not silently fall back to a paid model.

Optional OpenRouter metadata:

```env
OPENROUTER_SITE_URL=http://localhost:5173
OPENROUTER_APP_NAME=AI Interview Coach
```

### Groq Speech-To-Text

```env
TRANSCRIPTION_PROVIDER=groq
TRANSCRIPTION_API_KEY=your_groq_api_key_here
TRANSCRIPTION_BASE_URL=https://api.groq.com/openai/v1
TRANSCRIPTION_MODEL=whisper-large-v3
```

You can also use Groq's SDK-style variable:

```env
GROQ_API_KEY=your_groq_api_key_here
```

If `TRANSCRIPTION_API_KEY` is empty and `TRANSCRIPTION_PROVIDER=groq`, the backend uses `GROQ_API_KEY`.

### Backend

```env
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
DATA_DIR=./data
AGENT_DEBUG_LOGS=true
```

## Other Providers

The chat client is OpenAI-compatible. To use a different LLM provider, change:

```env
LLM_PROVIDER=custom
LLM_API_KEY=your_provider_key_here
LLM_BASE_URL=https://provider.example.com/v1
LLM_MODEL=your_model_name_here
```

The transcription service also posts to an OpenAI-compatible `/audio/transcriptions` endpoint. For another transcription provider, set:

```env
TRANSCRIPTION_PROVIDER=custom
TRANSCRIPTION_API_KEY=your_provider_key_here
TRANSCRIPTION_BASE_URL=https://provider.example.com/v1
TRANSCRIPTION_MODEL=your_transcription_model_here
```

## Run The App

Start the backend:

```powershell
cd F:\Hiring_manager\ai-interview-coach
.\.venv\Scripts\Activate.ps1
python backend\run_backend.py
```

Start the static frontend server in another terminal:

```powershell
cd F:\Hiring_manager\ai-interview-coach\frontend
python -m http.server 5173
```

Open:

```text
http://127.0.0.1:5173
```

Backend health check:

```text
http://127.0.0.1:8000/health
```

## How To Use

1. Upload or paste a job announcement.
2. Upload or paste a candidate profile/CV.
3. Optionally upload or paste custom agent instructions.
4. Choose the interview language mode.
5. Click **Start interview**.
6. Record an answer or type manually.
7. Transcribe the audio.
8. Edit the transcript.
9. Submit the answer for feedback.
10. Retry the same question if needed, or continue to the next question.

Evaluated answers are held as a pending attempt until **Next question** or **Save session** is clicked. Retrying the same question replaces the pending attempt.

## Templates

The `templates/` folder contains example Markdown files. They are not strict schemas. They are there to help users prepare high-quality inputs.

- `job_announcement_template.md`: structure for a role description, responsibilities, skills, technologies, and interview focus areas.
- `candidate_profile_template.md`: structure for CV, skills, projects, strengths, weaknesses, and preferred answer style.
- `agent_instructions_template.md`: instructions for how the AI hiring manager and coach should behave.
- `evaluation_rubric_template.md`: scoring guidance for clarity, relevance, structure, specificity, confidence, and language quality.
- `language_settings_template.md`: language behavior for English, Norwegian, auto, and mixed modes.

Users can write their own files in any style. The app reads `.txt` and `.md` files as plain text and sends the full text to the agents.

## API Overview

```text
GET  /health
GET  /config/public
POST /interview/start
POST /interview/next-question
POST /interview/evaluate-answer
POST /transcription/transcribe
GET  /sessions
GET  /sessions/{session_id}
POST /sessions/save
POST /debug/next-question
POST /debug/evaluate-answer
```

## Local Data And Debugging

Runtime data is generated locally under `data/` and is ignored by Git.

- Successful saved sessions: `data/sessions/{session_id}.json`
- Backend logs: `data/logs/backend.log`
- Failed evaluation debug files, when file writing is allowed: `data/sessions/_failed_evaluation_{timestamp}_{session_id}.json`

If the UI shows a `502` from the LLM provider, check:

- the backend terminal output
- browser DevTools Network response
- `POST /debug/next-question`
- `POST /debug/evaluate-answer`

LLM calls retry transient network/TLS failures using `LLM_MAX_RETRIES`.

## Why This Project Matters

This project demonstrates practical AI-agent application development:

- prompt-driven role simulation
- structured JSON outputs from LLMs
- provider-agnostic API design
- speech-to-text integration
- local persistence
- robust failure handling and retry UX
- a simple frontend focused on real user workflow rather than UI complexity

## Limitations

- Real LLM and transcription calls require provider API keys.
- Transcription is file-based, not streaming.
- Session storage is local JSON, not a database.
- The frontend is intentionally simple.

## Future Improvements

- Export sessions to Markdown or PDF.
- Add a richer session browser.
- Add optional per-turn debug view for question reasoning.
- Add more provider-specific transcription adapters.
- Add automated tests for retry and session-save behavior.
