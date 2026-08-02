"""Where raw configuration values come from.

This module is the single, exclusive place in the entire codebase
allowed to read ``os.environ``. Every other module — including the rest
of :mod:`velora.configuration` — reaches raw values only through the
:class:`ConfigSource` protocol, never through ``os.environ`` directly.
This invariant is enforced by ``tests/test_no_direct_environ_access.py``,
not just documented.
"""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable

__all__ = ["ConfigSource", "EnvironmentSource"]


@runtime_checkable
class ConfigSource(Protocol):
    """A source of raw, untyped configuration values, keyed by name.

    Implementations return ``None`` for an absent key — never raise.
    Turning "missing" into an error, and a raw string into a typed
    value, is the job of the parsing layer, not the source.
    """

    def get(self, key: str) -> str | None:
        """Return the raw value for ``key``, or ``None`` if absent."""
        ...  # pragma: no cover — structural signature, never executed


class EnvironmentSource:
    """A :class:`ConfigSource` backed by process environment variables."""

    def get(self, key: str) -> str | None:
        return os.environ.get(key)
