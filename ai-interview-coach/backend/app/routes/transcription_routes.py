from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from app.models import TranscriptionResponse
from app.services.transcription import TranscriptionService

router = APIRouter(prefix="/transcription")
service = TranscriptionService()


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(file: UploadFile = File(...)) -> TranscriptionResponse:
    return await service.transcribe(file)
