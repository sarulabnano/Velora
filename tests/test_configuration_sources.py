"""Tests for velora.configuration sources."""

from __future__ import annotations

from typing import TYPE_CHECKING

from velora.configuration import ConfigSource, EnvironmentSource

if TYPE_CHECKING:
    import pytest


def test_environment_source_reads_a_set_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VELORA_TEST_KEY", "some-value")

    assert EnvironmentSource().get("VELORA_TEST_KEY") == "some-value"


def test_environment_source_returns_none_for_unset_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("VELORA_TEST_KEY_UNSET", raising=False)

    assert EnvironmentSource().get("VELORA_TEST_KEY_UNSET") is None


def test_environment_source_is_recognized_as_config_source() -> None:
    assert isinstance(EnvironmentSource(), ConfigSource)


def test_object_without_get_is_not_a_config_source() -> None:
    assert not isinstance(object(), ConfigSource)
