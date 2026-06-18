from __future__ import annotations

import os

import uvicorn

from app.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=os.getenv("BACKEND_RELOAD", "false").lower() == "true",
    )


if __name__ == "__main__":
    main()
