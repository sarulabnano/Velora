"""Tests for velora.runtime.SystemClock."""

from __future__ import annotations

from datetime import UTC, datetime

from velora.runtime import Clock, SystemClock


def test_returns_a_timezone_aware_datetime() -> None:
    result = SystemClock().now()

    assert result.tzinfo is not None


def test_returns_a_value_close_to_the_real_current_time() -> None:
    before = datetime.now(UTC)
    result = SystemClock().now()
    after = datetime.now(UTC)

    assert before <= result <= after


def test_is_recognized_as_a_clock() -> None:
    assert isinstance(SystemClock(), Clock)


def test_services_system_clock_satisfies_runtimes_clock_protocol() -> None:
    """Structural typing (ADR-0007): no import between the two packages."""
    from velora.services import SystemClock as ServicesSystemClock

    assert isinstance(ServicesSystemClock(), Clock)
