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


def test_defaults_anthropic_api_key_to_none_when_unset() -> None:
    settings = VeloraSettings.from_source(_DictSource({}))

    assert settings.anthropic_api_key is None


def test_reads_anthropic_api_key_from_source() -> None:
    settings = VeloraSettings.from_source(
        _DictSource({"VELORA_ANTHROPIC_API_KEY": "sk-ant-test-value"})
    )

    assert settings.anthropic_api_key == "sk-ant-test-value"


def test_defaults_elevenlabs_api_key_to_none_when_unset() -> None:
    settings = VeloraSettings.from_source(_DictSource({}))

    assert settings.elevenlabs_api_key is None


def test_reads_elevenlabs_api_key_from_source() -> None:
    settings = VeloraSettings.from_source(
        _DictSource({"VELORA_ELEVENLABS_API_KEY": "el-test-value"})
    )

    assert settings.elevenlabs_api_key == "el-test-value"


def test_defaults_openai_api_key_to_none_when_unset() -> None:
    settings = VeloraSettings.from_source(_DictSource({}))

    assert settings.openai_api_key is None


def test_reads_openai_api_key_from_source() -> None:
    settings = VeloraSettings.from_source(_DictSource({"VELORA_OPENAI_API_KEY": "oa-test-value"}))

    assert settings.openai_api_key == "oa-test-value"


def test_settings_is_frozen() -> None:
    settings = VeloraSettings.from_source(_DictSource({}))

    with pytest.raises(dataclasses.FrozenInstanceError):
        settings.environment = Environment.PRODUCTION  # type: ignore[misc]
