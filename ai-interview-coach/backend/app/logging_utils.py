from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.config import get_settings

_CONFIGURED = False
_WARNED_NO_FILE_LOGGER = False


def configure_logging() -> None:
    global _CONFIGURED, _WARNED_NO_FILE_LOGGER
    if _CONFIGURED:
        return

    settings = get_settings()
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    log_path = settings.logs_dir / "backend.log"
    fallback_log_path = settings.sessions_dir / "_backend.log"
    try:
        settings.logs_dir.mkdir(parents=True, exist_ok=True)
        _add_file_handler(root_logger, log_path)
    except OSError:
        try:
            settings.sessions_dir.mkdir(parents=True, exist_ok=True)
            _add_file_handler(root_logger, fallback_log_path)
            root_logger.warning("Could not create file logger at %s; using %s.", log_path, fallback_log_path)
        except OSError:
            if not _WARNED_NO_FILE_LOGGER:
                root_logger.warning("Could not create a file logger; continuing with console logging only.")
                _WARNED_NO_FILE_LOGGER = True
    _CONFIGURED = True


def _add_file_handler(root_logger: logging.Logger, log_path) -> None:
    if any(isinstance(handler, RotatingFileHandler) and handler.baseFilename == str(log_path) for handler in root_logger.handlers):
        return
    file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
