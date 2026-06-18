from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.agents.hiring_manager import HiringManagerAgent
from app.agents.interview_coach import InterviewCoachAgent
from app.models import EvaluateAnswerRequest, NextQuestionRequest

router = APIRouter(prefix="/debug")
coach = InterviewCoachAgent()
hiring_manager = HiringManagerAgent()


@router.post("/next-question")
async def debug_next_question(request: NextQuestionRequest) -> JSONResponse:
    try:
        question = await hiring_manager.next_question(request.session)
        return JSONResponse(
            {
                "ok": True,
                "session_id": request.session.session_id,
                "question": question.model_dump(),
            }
        )
    except Exception as exc:
        return JSONResponse(
            {
                "ok": False,
                "session_id": request.session.session_id,
                "error_type": exc.__class__.__name__,
                "error_detail": getattr(exc, "detail", str(exc)),
                "turn_count": len(request.session.turns),
            },
            status_code=200,
        )


@router.post("/evaluate-answer")
async def debug_evaluate_answer(request: EvaluateAnswerRequest) -> JSONResponse:
    try:
        evaluation = await coach.evaluate(
            request.session,
            request.question,
            request.answer_transcript,
        )
        return JSONResponse(
            {
                "ok": True,
                "session_id": request.session.session_id,
                "evaluation": evaluation.model_dump(),
            }
        )
    except Exception as exc:
        return JSONResponse(
            {
                "ok": False,
                "session_id": request.session.session_id,
                "error_type": exc.__class__.__name__,
                "error_detail": getattr(exc, "detail", str(exc)),
                "question": request.question.model_dump() if request.question else None,
                "answer_transcript": request.answer_transcript,
            },
            status_code=200,
        )
