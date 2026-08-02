"""Tests for velora.configuration.LogLevel."""

from __future__ import annotations

from velora.configuration import LogLevel


def test_all_expected_members_exist() -> None:
    assert {member.name for member in LogLevel} == {
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    }


def test_members_have_distinct_lowercase_values() -> None:
    values = [member.value for member in LogLevel]
    assert len(values) == len(set(values))
    assert all(value == value.lower() for value in values)
