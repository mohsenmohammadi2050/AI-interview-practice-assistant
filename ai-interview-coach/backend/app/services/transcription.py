from __future__ import annotations

import httpx
from fastapi import HTTPException, UploadFile

from app.config import Settings, get_settings
from app.models import TranscriptionResponse


class TranscriptionService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def transcribe(self, audio_file: UploadFile) -> TranscriptionResponse:
        if not self.settings.transcription_api_key:
            raise HTTPException(
                status_code=500,
                detail="Missing transcription API key. Set TRANSCRIPTION_API_KEY or GROQ_API_KEY. You can type the answer manually instead.",
            )

        content = await audio_file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")

        headers = {"Authorization": f"Bearer {self.settings.transcription_api_key}"}
        files = {
            "file": (
                audio_file.filename or "answer.webm",
                content,
                audio_file.content_type or "audio/webm",
            )
        }
        data = {
            "model": self.settings.transcription_model,
            "temperature": "0",
            "response_format": "verbose_json",
        }

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.settings.transcription_base_url}/audio/transcriptions",
                    headers=headers,
                    files=files,
                    data=data,
                )
            response.raise_for_status()
            payload = response.json()
            return TranscriptionResponse(
                transcript=payload.get("text", ""),
                provider=self.settings.transcription_provider,
                model=self.settings.transcription_model,
            )
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:1000]
            raise HTTPException(status_code=502, detail=f"Transcription failed: {exc.response.status_code} {body}") from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Transcription failed: {exc}") from exc
