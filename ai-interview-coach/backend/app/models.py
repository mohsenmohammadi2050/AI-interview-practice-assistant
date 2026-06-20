from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


LanguageMode = Literal["english", "norwegian", "auto", "mixed"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentQuestion(BaseModel):
    question: str
    language: Literal["english", "norwegian", "mixed"] = "english"
    category: Literal[
        "motivation",
        "behavioral",
        "technical",
        "project",
        "role_fit",
        "communication",
        "follow_up",
    ] = "motivation"
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    reason_for_question: str = ""


class CoachScores(BaseModel):
    clarity: int = Field(ge=1, le=5)
    relevance: int = Field(ge=1, le=5)
    structure: int = Field(ge=1, le=5)
    specificity: int = Field(ge=1, le=5)
    confidence: int = Field(ge=1, le=5)
    language_quality: int = Field(ge=1, le=5)


class CoachEvaluation(BaseModel):
    overall_score: int = Field(ge=1, le=5)
    scores: CoachScores
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    improved_answer: str = ""
    speaking_tips: list[str] = Field(default_factory=list)
    next_focus: str = ""
    should_retry_question: bool = False


class SessionTurn(BaseModel):
    question: str
    question_metadata: dict[str, Any] = Field(default_factory=dict)
    answer_transcript: str = ""
    evaluation: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)


class InterviewSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    job_announcement: str
    candidate_profile: str
    hiring_manager_instructions: str = ""
    interview_coach_instructions: str = ""
    agent_instructions: str = ""
    language_mode: LanguageMode = "auto"
    turns: list[SessionTurn] = Field(default_factory=list)


class StartInterviewRequest(BaseModel):
    job_announcement: str
    candidate_profile: str
    hiring_manager_instructions: str = ""
    interview_coach_instructions: str = ""
    agent_instructions: str = ""
    language_mode: LanguageMode = "auto"


class StartInterviewResponse(BaseModel):
    session: InterviewSession
    question: AgentQuestion


class NextQuestionRequest(BaseModel):
    session: InterviewSession


class NextQuestionResponse(BaseModel):
    question: AgentQuestion


class EvaluateAnswerRequest(BaseModel):
    session: InterviewSession
    question: AgentQuestion | None = None
    answer_transcript: str


class EvaluateAnswerResponse(BaseModel):
    evaluation: CoachEvaluation
    session: InterviewSession


class TranscriptionResponse(BaseModel):
    transcript: str
    provider: str
    model: str


class SaveSessionRequest(BaseModel):
    session: InterviewSession


class PublicConfigResponse(BaseModel):
    llm_provider: str
    llm_base_url: str
    llm_model: str
    transcription_provider: str
    transcription_base_url: str
    transcription_model: str
