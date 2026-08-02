"""Tests for velora package-level metadata."""

from __future__ import annotations

from typing import TYPE_CHECKING

import velora

if TYPE_CHECKING:
    import pytest


def test_version_is_exposed_as_string() -> None:
    assert isinstance(velora.__version__, str)
    assert velora.__version__ != ""


def test_version_matches_installed_distribution_metadata() -> None:
    from importlib import metadata

    assert velora.__version__ == metadata.version("velora")


def test_public_surface_is_minimal() -> None:
    assert velora.__all__ == ["__version__"]


def test_resolve_version_falls_back_when_distribution_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from importlib import metadata as importlib_metadata

    def _raise_not_found(_name: str) -> str:
        raise importlib_metadata.PackageNotFoundError(_name)

    monkeypatch.setattr(importlib_metadata, "version", _raise_not_found)

    assert velora._resolve_version() == "0.0.0+unknown"
