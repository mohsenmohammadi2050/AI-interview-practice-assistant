from __future__ import annotations

import json
from pathlib import Path

from fastapi import HTTPException

from app.config import get_settings
from app.models import InterviewSession, SessionTurn, utc_now_iso


def _sessions_dir() -> Path:
    settings = get_settings()
    settings.sessions_dir.mkdir(parents=True, exist_ok=True)
    return settings.sessions_dir


def _session_path(session_id: str) -> Path:
    return _sessions_dir() / f"{session_id}.json"


def create_session(session: InterviewSession) -> InterviewSession:
    save_session(session)
    return session


def save_session(session: InterviewSession) -> InterviewSession:
    session.updated_at = utc_now_iso()
    path = _session_path(session.session_id)
    path.write_text(session.model_dump_json(indent=2), encoding="utf-8")
    return session


def get_session(session_id: str) -> InterviewSession:
    path = _session_path(session_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return InterviewSession.model_validate(data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not read session: {exc}") from exc


def list_sessions() -> list[InterviewSession]:
    sessions: list[InterviewSession] = []
    for path in sorted(_sessions_dir().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            sessions.append(InterviewSession.model_validate_json(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return sessions


def append_turn(session: InterviewSession, turn: SessionTurn) -> InterviewSession:
    session.turns.append(turn)
    return save_session(session)
