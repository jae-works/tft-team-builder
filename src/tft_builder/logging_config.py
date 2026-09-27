"""Application logging configuration."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_HANDLER_MARKER = "_tft_builder_managed_handler"


def _is_managed(handler: logging.Handler) -> bool:
    return bool(getattr(handler, _HANDLER_MARKER, False))


def _mark_managed(handler: logging.Handler) -> None:
    setattr(handler, _HANDLER_MARKER, True)


def _managed_file_path(logger: logging.Logger) -> Path | None:
    for handler in logger.handlers:
        if _is_managed(handler) and isinstance(handler, RotatingFileHandler):
            return Path(handler.baseFilename).resolve()
    return None


def _remove_managed_handlers(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        if not _is_managed(handler):
            continue
        logger.removeHandler(handler)
        handler.close()


def configure_logging(log_dir: Path, *, level: int = logging.INFO) -> Path:
    """Configure predictable console and rotating-file logging.

    Repeating the call for the same target only updates levels. If the runtime log directory
    changes, the managed handlers are replaced so the logger never silently continues writing
    to the previous location. Handlers attached by unrelated code are left untouched.
    """

    resolved_dir = Path(log_dir).expanduser().resolve()
    resolved_dir.mkdir(parents=True, exist_ok=True)
    log_path = resolved_dir / "app.log"

    logger = logging.getLogger("tft_builder")
    logger.setLevel(level)
    logger.propagate = False

    current_file = _managed_file_path(logger)
    managed_handlers = [handler for handler in logger.handlers if _is_managed(handler)]
    needs_rebuild = current_file != log_path or len(managed_handlers) != 2

    if needs_rebuild:
        _remove_managed_handlers(logger)
        formatter = logging.Formatter(LOG_FORMAT)

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level)
        stream_handler.setFormatter(formatter)
        _mark_managed(stream_handler)
        logger.addHandler(stream_handler)

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=2_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        _mark_managed(file_handler)
        logger.addHandler(file_handler)
    else:
        for handler in managed_handlers:
            handler.setLevel(level)

    return log_path
