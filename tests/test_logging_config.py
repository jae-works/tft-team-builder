from __future__ import annotations

import logging
from pathlib import Path

import pytest

from tft_builder.logging_config import configure_logging


@pytest.fixture(autouse=True)
def reset_application_logger() -> None:
    logger = logging.getLogger("tft_builder")
    original_handlers = list(logger.handlers)
    original_level = logger.level
    original_propagate = logger.propagate
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    try:
        yield
    finally:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close()
        for handler in original_handlers:
            logger.addHandler(handler)
        logger.setLevel(original_level)
        logger.propagate = original_propagate


def flush_application_handlers() -> None:
    for handler in logging.getLogger("tft_builder").handlers:
        handler.flush()


def test_configure_logging_creates_log_directory_and_file(tmp_path: Path) -> None:
    log_path = configure_logging(tmp_path / "logs")
    logger = logging.getLogger("tft_builder")
    logger.info("test message")
    flush_application_handlers()
    assert log_path.is_file()
    assert "test message" in log_path.read_text(encoding="utf-8")


def test_configure_logging_is_idempotent_for_same_directory(tmp_path: Path) -> None:
    configure_logging(tmp_path / "logs")
    logger = logging.getLogger("tft_builder")
    first_handlers = tuple(logger.handlers)
    configure_logging(tmp_path / "logs")
    assert tuple(logger.handlers) == first_handlers
    assert len(logger.handlers) == 2


def test_configure_logging_updates_logger_and_handler_levels(tmp_path: Path) -> None:
    configure_logging(tmp_path / "logs", level=logging.DEBUG)
    logger = logging.getLogger("tft_builder")
    assert logger.level == logging.DEBUG
    assert all(handler.level == logging.DEBUG for handler in logger.handlers)


def test_reconfigure_to_new_directory_writes_only_to_new_file(tmp_path: Path) -> None:
    first_path = configure_logging(tmp_path / "first")
    logger = logging.getLogger("tft_builder")
    logger.info("first target")
    flush_application_handlers()

    second_path = configure_logging(tmp_path / "second")
    logger.info("second target")
    flush_application_handlers()

    assert first_path != second_path
    assert "first target" in first_path.read_text(encoding="utf-8")
    assert "second target" not in first_path.read_text(encoding="utf-8")
    assert "second target" in second_path.read_text(encoding="utf-8")


def test_configure_logging_preserves_unmanaged_handlers(tmp_path: Path) -> None:
    logger = logging.getLogger("tft_builder")
    external = logging.NullHandler()
    logger.addHandler(external)

    configure_logging(tmp_path / "logs")
    configure_logging(tmp_path / "other")

    assert external in logger.handlers
    managed = [handler for handler in logger.handlers if handler is not external]
    assert len(managed) == 2
