from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def load_prompt(name: str) -> str:
    return (PROJECT_ROOT / "prompts" / name).read_text(encoding="utf-8")
