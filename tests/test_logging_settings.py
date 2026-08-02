"""Tests for velora.logging.LoggingSettings."""

from __future__ import annotations

import dataclasses

import pytest

from velora.logging import LoggingSettings, LogLevel


def test_holds_the_given_level() -> None:
    settings = LoggingSettings(level=LogLevel.WARNING)

    assert settings.level is LogLevel.WARNING


def test_is_frozen() -> None:
    settings = LoggingSettings(level=LogLevel.INFO)

    with pytest.raises(dataclasses.FrozenInstanceError):
        settings.level = LogLevel.ERROR  # type: ignore[misc]
