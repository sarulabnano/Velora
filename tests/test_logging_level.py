"""Tests for velora.logging.LogLevel."""

from __future__ import annotations

import logging as stdlib_logging

import pytest

from velora.logging import LogLevel


def test_all_expected_members_exist() -> None:
    assert {member.name for member in LogLevel} == {
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    }


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        (LogLevel.DEBUG, stdlib_logging.DEBUG),
        (LogLevel.INFO, stdlib_logging.INFO),
        (LogLevel.WARNING, stdlib_logging.WARNING),
        (LogLevel.ERROR, stdlib_logging.ERROR),
        (LogLevel.CRITICAL, stdlib_logging.CRITICAL),
    ],
)
def test_to_stdlib_level_maps_correctly(level: LogLevel, expected: int) -> None:
    assert level.to_stdlib_level() == expected


def test_importing_this_module_does_not_shadow_the_standard_library() -> None:
    assert stdlib_logging.__name__ == "logging"
    assert hasattr(stdlib_logging, "getLogger")
