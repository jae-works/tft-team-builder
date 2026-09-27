"""Application logging configuration."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_HANDLER_MARKER = "_tft_builder_managed_handler"


def _is_managed(handler: logging.Handler) -> bool:
    return bool(getattr(handler, _HANDLER_MARKER, False))


def _mark_managed(handler: logging.Handler) -> logging.Handler:
    setattr(handler, _HANDLER_MARKER, True)
    return handler


def _managed_handlers(logger: logging.Logger) -> list[logging.Handler]:
    return [handler for handler in logger.handlers if _is_managed(handler)]


def _managed_file_path(logger: logging.Logger) -> Path | None:
    for handler in _managed_handlers(logger):
        if isinstance(handler, RotatingFileHandler):
            return Path(handler.baseFilename).resolve()
    return None


def _remove_managed_handlers(logger: logging.Logger) -> None:
    for handler in list(_managed_handlers(logger)):
        logger.removeHandler(handler)
        handler.close()


def _create_managed_handlers(log_path: Path, level: int) -> tuple[logging.Handler, logging.Handler]:
    """Create both handlers before changing the active logger configuration."""

    formatter = logging.Formatter(LOG_FORMAT)
    stream_handler = _mark_managed(logging.StreamHandler())
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)

    try:
        file_handler = _mark_managed(
            RotatingFileHandler(
                log_path,
                maxBytes=2_000_000,
                backupCount=3,
                encoding="utf-8",
            )
        )
    except Exception:
        stream_handler.close()
        raise

    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    return stream_handler, file_handler


def configure_logging(log_dir: Path, *, level: int = logging.INFO) -> Path:
    """Configure predictable console and rotating-file logging.

    Repeating the call for the same target only updates managed handler levels. If the target
    directory changes, replacement handlers are fully constructed before the old handlers are
    removed. A failed reconfiguration therefore leaves the previous working logger intact.
    Handlers attached by pytest, libraries, or other application code are never modified.
    """

    resolved_dir = Path(log_dir).expanduser().resolve()
    resolved_dir.mkdir(parents=True, exist_ok=True)
    log_path = resolved_dir / "app.log"

    logger = logging.getLogger("tft_builder")
    managed = _managed_handlers(logger)
    current_file = _managed_file_path(logger)
    needs_rebuild = current_file != log_path or len(managed) != 2

    if needs_rebuild:
        replacement = _create_managed_handlers(log_path, level)
        _remove_managed_handlers(logger)
        for handler in replacement:
            logger.addHandler(handler)
    else:
        for handler in managed:
            handler.setLevel(level)

    logger.setLevel(level)
    logger.propagate = False
    return log_path
