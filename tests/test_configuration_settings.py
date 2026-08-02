"""Tests for velora.configuration.VeloraSettings."""

from __future__ import annotations

import dataclasses

import pytest

from velora.configuration import (
    Environment,
    InvalidConfigurationValueError,
    LogLevel,
    VeloraSettings,
)


class _DictSource:
    def __init__(self, values: dict[str, str]) -> None:
        self._values = values

    def get(self, key: str) -> str | None:
        return self._values.get(key)


def test_defaults_to_development_when_unset() -> None:
    settings = VeloraSettings.from_source(_DictSource({}))

    assert settings.environment is Environment.DEVELOPMENT


def test_defaults_log_level_to_info_when_unset() -> None:
    settings = VeloraSettings.from_source(_DictSource({}))

    assert settings.log_level is LogLevel.INFO


def test_reads_environment_from_source() -> None:
    settings = VeloraSettings.from_source(_DictSource({"VELORA_ENVIRONMENT": "production"}))

    assert settings.environment is Environment.PRODUCTION


def test_reads_log_level_from_source() -> None:
    settings = VeloraSettings.from_source(_DictSource({"VELORA_LOG_LEVEL": "debug"}))

    assert settings.log_level is LogLevel.DEBUG


def test_invalid_environment_value_raises() -> None:
    source = _DictSource({"VELORA_ENVIRONMENT": "not-a-real-environment"})

    with pytest.raises(InvalidConfigurationValueError):
        VeloraSettings.from_source(source)


def test_invalid_log_level_value_raises() -> None:
    source = _DictSource({"VELORA_LOG_LEVEL": "not-a-real-level"})

    with pytest.raises(InvalidConfigurationValueError):
        VeloraSettings.from_source(source)


def test_settings_is_frozen() -> None:
    settings = VeloraSettings.from_source(_DictSource({}))

    with pytest.raises(dataclasses.FrozenInstanceError):
        settings.environment = Environment.PRODUCTION  # type: ignore[misc]
