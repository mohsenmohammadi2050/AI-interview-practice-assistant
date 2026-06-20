from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import HTTPException

from app.agents.hiring_manager import HiringManagerAgent
from app.agents.interview_coach import InterviewCoachAgent
from app.models import (
    EvaluateAnswerRequest,
    EvaluateAnswerResponse,
    InterviewSession,
    NextQuestionResponse,
    StartInterviewRequest,
    StartInterviewResponse,
)
from app.storage import create_session
from app.config import get_settings
from app.logging_utils import get_logger


logger = get_logger(__name__)


def _validate_required_text(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail=f"{field_name} cannot be empty.")
    return cleaned


class SessionService:
    def __init__(
        self,
        hiring_manager: HiringManagerAgent | None = None,
        coach: InterviewCoachAgent | None = None,
    ) -> None:
        self.hiring_manager = hiring_manager or HiringManagerAgent()
        self.coach = coach or InterviewCoachAgent()

    async def start(self, request: StartInterviewRequest) -> StartInterviewResponse:
        session = InterviewSession(
            job_announcement=_validate_required_text(request.job_announcement, "Job announcement"),
            candidate_profile=_validate_required_text(request.candidate_profile, "Candidate profile"),
            hiring_manager_instructions=(
                request.hiring_manager_instructions.strip() or request.agent_instructions.strip()
            ),
            interview_coach_instructions=(
                request.interview_coach_instructions.strip() or request.agent_instructions.strip()
            ),
            agent_instructions=request.agent_instructions.strip(),
            language_mode=request.language_mode,
        )
        question = await self.hiring_manager.next_question(session)
        create_session(session)
        return StartInterviewResponse(session=session, question=question)

    async def next_question(self, session: InterviewSession) -> NextQuestionResponse:
        question = await self.hiring_manager.next_question(session)
        return NextQuestionResponse(question=question)

    async def evaluate(self, request: EvaluateAnswerRequest) -> EvaluateAnswerResponse:
        answer = _validate_required_text(request.answer_transcript, "Answer transcript")
        try:
            evaluation = await self.coach.evaluate(request.session, request.question, answer)
        except Exception as exc:
            self._save_failed_evaluation_debug(request, answer, exc)
            logger.exception(
                "Evaluation failed session_id=%s question_present=%s answer_chars=%s",
                request.session.session_id,
                request.question is not None,
                len(answer),
            )
            raise
        return EvaluateAnswerResponse(evaluation=evaluation, session=request.session)

    def _save_failed_evaluation_debug(
        self,
        request: EvaluateAnswerRequest,
        answer: str,
        exc: Exception,
    ) -> None:
        settings = get_settings()
        if not settings.agent_debug_logs:
            return

        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            path = settings.sessions_dir / f"_failed_evaluation_{timestamp}_{request.session.session_id}.json"
            error_detail = getattr(exc, "detail", str(exc))
            payload = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "session_id": request.session.session_id,
                "language_mode": request.session.language_mode,
                "question": request.question.model_dump() if request.question else None,
                "answer_transcript": answer,
                "error_type": exc.__class__.__name__,
                "error_detail": error_detail,
                "turn_count_before_failure": len(request.session.turns),
            }
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            logger.exception("Could not write failed evaluation debug file")
