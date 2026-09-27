from __future__ import annotations

import logging
from collections.abc import Iterator
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest

from tft_builder.logging_config import configure_logging


def managed_handlers(logger: logging.Logger) -> list[logging.Handler]:
    return [
        handler
        for handler in logger.handlers
        if getattr(handler, "_tft_builder_managed_handler", False)
    ]


def flush_managed_handlers() -> None:
    for handler in managed_handlers(logging.getLogger("tft_builder")):
        handler.flush()


def close_managed_handlers() -> None:
    logger = logging.getLogger("tft_builder")
    for handler in list(managed_handlers(logger)):
        logger.removeHandler(handler)
        handler.close()


@pytest.fixture(autouse=True)
def restore_logger_state() -> Iterator[None]:
    logger = logging.getLogger("tft_builder")
    original_level = logger.level
    original_propagate = logger.propagate
    try:
        yield
    finally:
        close_managed_handlers()
        logger.setLevel(original_level)
        logger.propagate = original_propagate


def test_configure_logging_creates_log_directory_and_file(tmp_path: Path) -> None:
    log_path = configure_logging(tmp_path / "logs")
    logger = logging.getLogger("tft_builder")
    logger.info("test message")
    flush_managed_handlers()

    assert log_path.is_file()
    assert "test message" in log_path.read_text(encoding="utf-8")


def test_configure_logging_creates_exactly_two_managed_handlers(tmp_path: Path) -> None:
    configure_logging(tmp_path / "logs")
    handlers = managed_handlers(logging.getLogger("tft_builder"))

    assert len(handlers) == 2
    assert sum(isinstance(handler, RotatingFileHandler) for handler in handlers) == 1


def test_configure_logging_is_idempotent_for_same_directory(tmp_path: Path) -> None:
    configure_logging(tmp_path / "logs")
    logger = logging.getLogger("tft_builder")
    first_handlers = tuple(managed_handlers(logger))

    configure_logging(tmp_path / "logs")

    assert tuple(managed_handlers(logger)) == first_handlers


def test_configure_logging_updates_only_managed_handler_levels(tmp_path: Path) -> None:
    logger = logging.getLogger("tft_builder")
    external = logging.NullHandler(level=logging.ERROR)
    logger.addHandler(external)
    try:
        configure_logging(tmp_path / "logs", level=logging.DEBUG)
        assert logger.level == logging.DEBUG
        assert all(handler.level == logging.DEBUG for handler in managed_handlers(logger))
        assert external.level == logging.ERROR
    finally:
        logger.removeHandler(external)


def test_reconfigure_to_new_directory_writes_only_to_new_file(tmp_path: Path) -> None:
    first_path = configure_logging(tmp_path / "first")
    logger = logging.getLogger("tft_builder")
    logger.info("first target")
    flush_managed_handlers()

    second_path = configure_logging(tmp_path / "second")
    logger.info("second target")
    flush_managed_handlers()

    assert first_path != second_path
    assert "first target" in first_path.read_text(encoding="utf-8")
    assert "second target" not in first_path.read_text(encoding="utf-8")
    assert "second target" in second_path.read_text(encoding="utf-8")


def test_configure_logging_preserves_unmanaged_handlers(tmp_path: Path) -> None:
    logger = logging.getLogger("tft_builder")
    external = logging.NullHandler()
    logger.addHandler(external)
    try:
        configure_logging(tmp_path / "logs")
        configure_logging(tmp_path / "other")
        assert external in logger.handlers
        assert len(managed_handlers(logger)) == 2
    finally:
        logger.removeHandler(external)


def test_configure_logging_preserves_pytest_capture_handlers(tmp_path: Path) -> None:
    logger = logging.getLogger("tft_builder")
    unmanaged_before = tuple(
        handler for handler in logger.handlers if handler not in managed_handlers(logger)
    )

    configure_logging(tmp_path / "logs")

    unmanaged_after = tuple(
        handler for handler in logger.handlers if handler not in managed_handlers(logger)
    )
    assert unmanaged_after == unmanaged_before


def test_configure_logging_disables_propagation(tmp_path: Path) -> None:
    logger = logging.getLogger("tft_builder")
    configure_logging(tmp_path / "logs")
    assert logger.propagate is False


def test_failed_reconfiguration_preserves_previous_managed_handlers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import tft_builder.logging_config as logging_config

    first_path = configure_logging(tmp_path / "first")
    logger = logging.getLogger("tft_builder")
    previous_handlers = tuple(managed_handlers(logger))

    class BrokenFileHandler:
        def __init__(self, *args, **kwargs) -> None:
            raise OSError("simulated file handler failure")

    monkeypatch.setattr(logging_config, "RotatingFileHandler", BrokenFileHandler)
    with pytest.raises(OSError, match="simulated"):
        configure_logging(tmp_path / "second")

    assert tuple(managed_handlers(logger)) == previous_handlers
    logger.info("still using first target")
    flush_managed_handlers()
    assert "still using first target" in first_path.read_text(encoding="utf-8")
