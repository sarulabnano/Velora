"""Tests for velora.runtime.RuntimeState."""

from __future__ import annotations

from velora.runtime import RuntimeState


def test_all_expected_states_exist() -> None:
    assert {member.name for member in RuntimeState} == {
        "NOT_STARTED",
        "STARTING",
        "RUNNING",
        "STOPPING",
        "STOPPED",
        "FAILED",
    }


def test_states_have_distinct_values() -> None:
    values = [member.value for member in RuntimeState]
    assert len(values) == len(set(values))
