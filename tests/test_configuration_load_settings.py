"""Tests for velora.configuration.load_settings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from velora.configuration import Environment, LogLevel, load_settings

if TYPE_CHECKING:
    import pytest


class _DictSource:
    def __init__(self, values: dict[str, str]) -> None:
        self._values = values

    def get(self, key: str) -> str | None:
        return self._values.get(key)


def test_uses_injected_source_when_given() -> None:
    settings = load_settings(_DictSource({"VELORA_ENVIRONMENT": "staging"}))

    assert settings.environment is Environment.STAGING


def test_reads_log_level_from_injected_source() -> None:
    settings = load_settings(_DictSource({"VELORA_LOG_LEVEL": "warning"}))

    assert settings.log_level is LogLevel.WARNING


def test_defaults_to_environment_source(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VELORA_ENVIRONMENT", "production")

    settings = load_settings()

    assert settings.environment is Environment.PRODUCTION


def test_default_source_falls_back_to_development(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VELORA_ENVIRONMENT", raising=False)

    settings = load_settings()

    assert settings.environment is Environment.DEVELOPMENT
