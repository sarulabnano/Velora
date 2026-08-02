"""Tests for velora.configuration._parsing.parse_enum."""

from __future__ import annotations

import pytest

from velora.configuration import (
    Environment,
    InvalidConfigurationValueError,
    MissingConfigurationValueError,
)
from velora.configuration._parsing import parse_enum


class _DictSource:
    def __init__(self, values: dict[str, str]) -> None:
        self._values = values

    def get(self, key: str) -> str | None:
        return self._values.get(key)


def test_parses_exact_match() -> None:
    source = _DictSource({"ENV": "PRODUCTION"})

    assert parse_enum(source, "ENV", Environment) == Environment.PRODUCTION


def test_parses_case_insensitively() -> None:
    source = _DictSource({"ENV": "production"})

    assert parse_enum(source, "ENV", Environment) == Environment.PRODUCTION


def test_strips_surrounding_whitespace() -> None:
    source = _DictSource({"ENV": "  staging  "})

    assert parse_enum(source, "ENV", Environment) == Environment.STAGING


def test_missing_key_without_default_raises() -> None:
    source = _DictSource({})

    with pytest.raises(MissingConfigurationValueError, match="ENV"):
        parse_enum(source, "ENV", Environment)


def test_missing_key_with_default_returns_default() -> None:
    source = _DictSource({})

    result = parse_enum(source, "ENV", Environment, default=Environment.DEVELOPMENT)

    assert result is Environment.DEVELOPMENT


def test_invalid_value_raises_with_valid_options_listed() -> None:
    source = _DictSource({"ENV": "not-a-real-environment"})

    with pytest.raises(InvalidConfigurationValueError) as exc_info:
        parse_enum(source, "ENV", Environment)

    message = str(exc_info.value)
    assert "not-a-real-environment" in message
    assert "DEVELOPMENT" in message
    assert "STAGING" in message
    assert "PRODUCTION" in message


def test_invalid_value_chains_the_original_key_error() -> None:
    source = _DictSource({"ENV": "bogus"})

    with pytest.raises(InvalidConfigurationValueError) as exc_info:
        parse_enum(source, "ENV", Environment)

    assert isinstance(exc_info.value.__cause__, KeyError)
