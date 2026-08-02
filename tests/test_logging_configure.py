"""Tests for velora.logging.configure_logging."""

from __future__ import annotations

import io

from velora.logging import LoggingSettings, LogLevel, RuntimeEventLogger, configure_logging
from velora.runtime import RuntimeEvent, RuntimeEventKind


def test_returns_a_runtime_event_logger() -> None:
    logger = configure_logging(LoggingSettings(level=LogLevel.INFO))

    assert isinstance(logger, RuntimeEventLogger)


def test_respects_injected_stream() -> None:
    stream = io.StringIO()

    logger = configure_logging(LoggingSettings(level=LogLevel.INFO), stream=stream)
    logger.on_runtime_event(RuntimeEvent(kind=RuntimeEventKind.BOOTSTRAP_STARTING))

    assert "bootstrap starting" in stream.getvalue()
