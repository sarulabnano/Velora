"""Tests for velora.runtime event model."""

from __future__ import annotations

import dataclasses

import pytest

from velora.runtime import RuntimeEvent, RuntimeEventKind, RuntimeEventListener


def test_event_defaults_have_no_component_or_error() -> None:
    event = RuntimeEvent(kind=RuntimeEventKind.BOOTSTRAP_STARTING)

    assert event.component_name is None
    assert event.error is None


def test_event_carries_component_name_and_error() -> None:
    error = ValueError("boom")

    event = RuntimeEvent(
        kind=RuntimeEventKind.FATAL_ERROR,
        component_name="database",
        error=error,
    )

    assert event.component_name == "database"
    assert event.error is error


def test_event_is_frozen() -> None:
    event = RuntimeEvent(kind=RuntimeEventKind.BOOTSTRAP_STARTING)

    with pytest.raises(dataclasses.FrozenInstanceError):
        event.component_name = "changed"  # type: ignore[misc]


def test_event_kinds_cover_full_lifecycle() -> None:
    assert {member.name for member in RuntimeEventKind} == {
        "BOOTSTRAP_STARTING",
        "BOOTSTRAP_COMPLETED",
        "COMPONENT_STARTING",
        "COMPONENT_STARTED",
        "COMPONENT_STOPPING",
        "COMPONENT_STOPPED",
        "SHUTDOWN_STARTING",
        "SHUTDOWN_COMPLETED",
        "FATAL_ERROR",
    }


class _Listener:
    def __init__(self) -> None:
        self.received: list[RuntimeEvent] = []

    def on_runtime_event(self, event: RuntimeEvent) -> None:
        self.received.append(event)


def test_object_implementing_protocol_is_recognized_as_listener() -> None:
    listener = _Listener()

    assert isinstance(listener, RuntimeEventListener)


def test_object_without_method_is_not_a_listener() -> None:
    assert not isinstance(object(), RuntimeEventListener)
