"""Velora — a composable, ten-year-stable AI platform runtime.

This package intentionally exposes a minimal public surface. During the
Foundation phase, only project metadata is available. The Runtime, and
everything built on top of it, will be introduced in subsequent phases
without breaking this entrypoint.
"""

from __future__ import annotations

from importlib import metadata as _metadata

__all__ = ["__version__"]


def _resolve_version() -> str:
    """Resolve the installed package version from distribution metadata.

    The version has a single source of truth: the `version` field in
    `pyproject.toml`. It is never duplicated as a literal in source code.
    """
    try:
        return _metadata.version("velora")
    except _metadata.PackageNotFoundError:
        return "0.0.0+unknown"


__version__: str = _resolve_version()
