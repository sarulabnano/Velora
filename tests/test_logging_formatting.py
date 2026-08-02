"""Tests for velora.logging._formatting.format_event."""

from __future__ import annotations

import pytest

from velora.logging._formatting import format_event
from velora.runtime import RuntimeEvent, RuntimeEventKind


def test_bootstrap_starting() -> None:
    message = format_event(RuntimeEvent(kind=RuntimeEventKind.BOOTSTRAP_STARTING))

    assert message == "runtime bootstrap starting"


def test_bootstrap_completed() -> None:
    message = format_event(RuntimeEvent(kind=RuntimeEventKind.BOOTSTRAP_COMPLETED))

    assert message == "runtime bootstrap completed"


def test_shutdown_starting() -> None:
    message = format_event(RuntimeEvent(kind=RuntimeEventKind.SHUTDOWN_STARTING))

    assert message == "runtime shutdown starting"


def test_shutdown_completed() -> None:
    message = format_event(RuntimeEvent(kind=RuntimeEventKind.SHUTDOWN_COMPLETED))

    assert message == "runtime shutdown completed"


@pytest.mark.parametrize(
    ("kind", "expected_verb"),
    [
        (RuntimeEventKind.COMPONENT_STARTING, "starting"),
        (RuntimeEventKind.COMPONENT_STARTED, "started"),
        (RuntimeEventKind.COMPONENT_STOPPING, "stopping"),
        (RuntimeEventKind.COMPONENT_STOPPED, "stopped"),
    ],
)
def test_component_lifecycle_messages_include_component_name(
    kind: RuntimeEventKind, expected_verb: str
) -> None:
    message = format_event(RuntimeEvent(kind=kind, component_name="database"))

    assert message == f"component 'database' {expected_verb}"


def test_fatal_error_with_component_includes_component_and_error() -> None:
    error = ValueError("boom")

    message = format_event(
        RuntimeEvent(kind=RuntimeEventKind.FATAL_ERROR, component_name="database", error=error)
    )

    assert message == "fatal error in component 'database': boom"


def test_fatal_error_without_component_omits_component_clause() -> None:
    error = ValueError("boom")

    message = format_event(RuntimeEvent(kind=RuntimeEventKind.FATAL_ERROR, error=error))

    assert message == "fatal error: boom"


def test_covers_every_runtime_event_kind() -> None:
    for kind in RuntimeEventKind:
        # Must not raise for any current kind — this is what makes
        # format_event (and therefore RuntimeEventLogger) total.
        format_event(RuntimeEvent(kind=kind, component_name="x", error=ValueError("x")))
