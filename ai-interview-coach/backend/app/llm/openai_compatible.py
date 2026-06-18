from __future__ import annotations

import asyncio
import time

import httpx
from fastapi import HTTPException

from app.config import Settings, get_settings
from app.logging_utils import get_logger


logger = get_logger(__name__)


class OpenAICompatibleChatClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _headers(self) -> dict[str, str]:
        if not self.settings.llm_api_key:
            raise HTTPException(status_code=500, detail="Missing LLM_API_KEY. Configure .env before using AI features.")
        if not self.settings.llm_model:
            raise HTTPException(status_code=500, detail="Missing LLM_MODEL. Set an explicit model in .env to avoid accidental provider defaults or paid fallback models.")

        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        if self.settings.llm_provider.lower() == "openrouter":
            headers["HTTP-Referer"] = self.settings.openrouter_site_url
            headers["X-Title"] = self.settings.openrouter_app_name
        return headers

    async def complete(self, messages: list[dict[str, str]], json_mode: bool = False) -> str:
        started = time.perf_counter()
        payload: dict[str, object] = {
            "model": self.settings.llm_model,
            "messages": messages,
            "temperature": 0.4,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        last_transport_error: httpx.TransportError | None = None
        for attempt in range(1, self.settings.llm_max_retries + 1):
            try:
                return await self._post_chat_completion(payload, json_mode, started, attempt)
            except httpx.TransportError as exc:
                last_transport_error = exc
                elapsed = time.perf_counter() - started
                logger.warning(
                    "LLM transport error provider=%s model=%s attempt=%s/%s elapsed=%.2fs error=%s",
                    self.settings.llm_provider,
                    self.settings.llm_model,
                    attempt,
                    self.settings.llm_max_retries,
                    elapsed,
                    exc,
                )
                if attempt >= self.settings.llm_max_retries:
                    break
                await asyncio.sleep(min(0.75 * attempt, 3.0))

        logger.exception("LLM request failed after transport retries", exc_info=last_transport_error)
        raise HTTPException(
            status_code=502,
            detail=(
                "LLM request failed after retrying a transient network/TLS error. "
                f"Last error: {last_transport_error}"
            ),
        )

    async def _post_chat_completion(
        self,
        payload: dict[str, object],
        json_mode: bool,
        started: float,
        attempt: int,
    ) -> str:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.settings.llm_base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
            response.raise_for_status()
            data = response.json()
            elapsed = time.perf_counter() - started
            logger.info(
                "LLM request succeeded provider=%s model=%s json_mode=%s elapsed=%.2fs",
                self.settings.llm_provider,
                self.settings.llm_model,
                json_mode,
                elapsed,
            )
            return data["choices"][0]["message"]["content"]
        except httpx.TransportError:
            raise
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:1000]
            elapsed = time.perf_counter() - started
            logger.error(
                "LLM request failed provider=%s model=%s status=%s attempt=%s elapsed=%.2fs body=%s",
                self.settings.llm_provider,
                self.settings.llm_model,
                exc.response.status_code,
                attempt,
                elapsed,
                body,
            )
            raise HTTPException(status_code=502, detail=f"LLM request failed: {exc.response.status_code} {body}") from exc
        except KeyError as exc:
            logger.exception("LLM response did not include assistant content")
            raise HTTPException(status_code=502, detail="LLM response did not include assistant content.") from exc
        except Exception as exc:
            logger.exception("LLM request failed before receiving a valid response")
            raise HTTPException(status_code=502, detail=f"LLM request failed: {exc}") from exc
