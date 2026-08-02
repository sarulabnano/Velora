"""Tests for velora.logging.RuntimeEventLogger."""

from __future__ import annotations

import io
import logging as stdlib_logging

from velora.logging import LoggingSettings, LogLevel, RuntimeEventLogger
from velora.runtime import RuntimeEvent, RuntimeEventKind, RuntimeEventListener


def test_is_recognized_as_a_runtime_event_listener() -> None:
    logger = RuntimeEventLogger(LoggingSettings(level=LogLevel.INFO))

    assert isinstance(logger, RuntimeEventListener)


def test_lifecycle_event_is_written_at_info_level() -> None:
    stream = io.StringIO()
    logger = RuntimeEventLogger(LoggingSettings(level=LogLevel.INFO), stream=stream)

    logger.on_runtime_event(RuntimeEvent(kind=RuntimeEventKind.BOOTSTRAP_STARTING))

    output = stream.getvalue()
    assert "INFO" in output
    assert "runtime bootstrap starting" in output


def test_fatal_error_is_written_at_error_level() -> None:
    stream = io.StringIO()
    logger = RuntimeEventLogger(LoggingSettings(level=LogLevel.INFO), stream=stream)

    logger.on_runtime_event(
        RuntimeEvent(kind=RuntimeEventKind.FATAL_ERROR, error=ValueError("boom"))
    )

    output = stream.getvalue()
    assert "ERROR" in output
    assert "boom" in output


def test_events_below_configured_level_are_suppressed() -> None:
    stream = io.StringIO()
    logger = RuntimeEventLogger(LoggingSettings(level=LogLevel.ERROR), stream=stream)

    logger.on_runtime_event(RuntimeEvent(kind=RuntimeEventKind.BOOTSTRAP_STARTING))

    assert stream.getvalue() == ""


def test_events_at_or_above_configured_level_are_emitted() -> None:
    stream = io.StringIO()
    logger = RuntimeEventLogger(LoggingSettings(level=LogLevel.ERROR), stream=stream)

    logger.on_runtime_event(
        RuntimeEvent(kind=RuntimeEventKind.FATAL_ERROR, error=ValueError("boom"))
    )

    assert "boom" in stream.getvalue()


def test_two_instances_with_the_same_name_do_not_share_state() -> None:
    stream_a = io.StringIO()
    stream_b = io.StringIO()
    logger_a = RuntimeEventLogger(LoggingSettings(level=LogLevel.INFO), stream=stream_a, name="x")
    RuntimeEventLogger(LoggingSettings(level=LogLevel.INFO), stream=stream_b, name="x")

    logger_a.on_runtime_event(RuntimeEvent(kind=RuntimeEventKind.BOOTSTRAP_STARTING))

    assert "bootstrap starting" in stream_a.getvalue()
    assert stream_b.getvalue() == ""


def test_does_not_register_in_the_global_logging_manager() -> None:
    unique_name = "velora-test-isolation-probe"

    RuntimeEventLogger(LoggingSettings(level=LogLevel.INFO), name=unique_name)

    assert unique_name not in stdlib_logging.Logger.manager.loggerDict
