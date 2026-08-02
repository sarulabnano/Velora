"""Tests for velora.configuration.Environment."""

from __future__ import annotations

from velora.configuration import Environment


def test_all_expected_members_exist() -> None:
    assert {member.name for member in Environment} == {
        "DEVELOPMENT",
        "STAGING",
        "PRODUCTION",
    }


def test_members_have_distinct_lowercase_values() -> None:
    values = [member.value for member in Environment]
    assert len(values) == len(set(values))
    assert all(value == value.lower() for value in values)
