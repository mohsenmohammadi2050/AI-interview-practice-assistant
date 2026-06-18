from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


def _load_env_files() -> None:
    project_root = Path(__file__).resolve().parents[2]
    for env_path in (project_root / ".env", project_root / ".env.local"):
        if env_path.exists():
            load_dotenv(env_path, override=False)


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    llm_max_retries: int
    openrouter_site_url: str
    openrouter_app_name: str
    transcription_provider: str
    transcription_api_key: str
    transcription_base_url: str
    transcription_model: str
    backend_host: str
    backend_port: int
    data_dir: Path
    agent_debug_logs: bool

    @property
    def sessions_dir(self) -> Path:
        return self.data_dir / "sessions"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"

    @property
    def evaluation_failures_dir(self) -> Path:
        return self.data_dir / "debug" / "evaluation_failures"


@lru_cache
def get_settings() -> Settings:
    _load_env_files()
    project_root = Path(__file__).resolve().parents[2]
    data_dir = Path(os.getenv("DATA_DIR", str(project_root / "data")))
    if not data_dir.is_absolute():
        data_dir = project_root / data_dir
    transcription_provider = os.getenv("TRANSCRIPTION_PROVIDER", "groq")
    transcription_api_key = os.getenv("TRANSCRIPTION_API_KEY", "")
    if not transcription_api_key and transcription_provider.lower() == "groq":
        transcription_api_key = os.getenv("GROQ_API_KEY", "")

    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "openrouter"),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_base_url=os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/"),
        llm_model=os.getenv("LLM_MODEL", ""),
        llm_max_retries=max(1, int(os.getenv("LLM_MAX_RETRIES", "3"))),
        openrouter_site_url=os.getenv("OPENROUTER_SITE_URL", "http://localhost:5173"),
        openrouter_app_name=os.getenv("OPENROUTER_APP_NAME", "AI Interview Coach"),
        transcription_provider=transcription_provider,
        transcription_api_key=transcription_api_key,
        transcription_base_url=os.getenv("TRANSCRIPTION_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/"),
        transcription_model=os.getenv("TRANSCRIPTION_MODEL", "whisper-large-v3"),
        backend_host=os.getenv("BACKEND_HOST", "127.0.0.1"),
        backend_port=int(os.getenv("BACKEND_PORT", "8000")),
        data_dir=data_dir,
        agent_debug_logs=os.getenv("AGENT_DEBUG_LOGS", "true").lower() == "true",
    )
