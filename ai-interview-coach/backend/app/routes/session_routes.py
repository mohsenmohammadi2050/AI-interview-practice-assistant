from __future__ import annotations

from fastapi import APIRouter

from app.models import InterviewSession, SaveSessionRequest
from app.storage import get_session, list_sessions, save_session

router = APIRouter(prefix="/sessions")


@router.get("", response_model=list[InterviewSession])
async def sessions() -> list[InterviewSession]:
    return list_sessions()


@router.get("/{session_id}", response_model=InterviewSession)
async def session_by_id(session_id: str) -> InterviewSession:
    return get_session(session_id)


@router.post("/save", response_model=InterviewSession)
async def save(request: SaveSessionRequest) -> InterviewSession:
    return save_session(request.session)
