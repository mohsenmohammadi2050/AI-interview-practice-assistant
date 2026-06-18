from __future__ import annotations

from fastapi import APIRouter

from app.models import (
    EvaluateAnswerRequest,
    EvaluateAnswerResponse,
    NextQuestionRequest,
    NextQuestionResponse,
    StartInterviewRequest,
    StartInterviewResponse,
)
from app.services.session_service import SessionService

router = APIRouter(prefix="/interview")
service = SessionService()


@router.post("/start", response_model=StartInterviewResponse)
async def start_interview(request: StartInterviewRequest) -> StartInterviewResponse:
    return await service.start(request)


@router.post("/next-question", response_model=NextQuestionResponse)
async def next_question(request: NextQuestionRequest) -> NextQuestionResponse:
    return await service.next_question(request.session)


@router.post("/evaluate-answer", response_model=EvaluateAnswerResponse)
async def evaluate_answer(request: EvaluateAnswerRequest) -> EvaluateAnswerResponse:
    return await service.evaluate(request)
