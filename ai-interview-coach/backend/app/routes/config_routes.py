from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.models import PublicConfigResponse

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/config/public", response_model=PublicConfigResponse)
async def public_config() -> PublicConfigResponse:
    settings = get_settings()
    return PublicConfigResponse(
        llm_provider=settings.llm_provider,
        llm_base_url=settings.llm_base_url,
        llm_model=settings.llm_model,
        transcription_provider=settings.transcription_provider,
        transcription_base_url=settings.transcription_base_url,
        transcription_model=settings.transcription_model,
    )
