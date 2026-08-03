"""Tests for velora.services.SystemClock."""

from __future__ import annotations

from datetime import UTC, datetime

from velora.services import Clock, SystemClock


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


def test_object_without_now_is_not_a_clock() -> None:
    assert not isinstance(object(), Clock)
