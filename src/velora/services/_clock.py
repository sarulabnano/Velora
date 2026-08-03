"""A Service abstracting "the current time".

This type never imports ``velora.runtime``. It satisfies
``velora.runtime.Clock`` structurally (same method signature) purely by
shape — Python's structural (PEP 544) typing means no inheritance or
import is needed for that to type-check under mypy. See ADR-0007.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

__all__ = ["Clock", "SystemClock"]


@runtime_checkable
class Clock(Protocol):
    """A source of the current time."""

    def now(self) -> datetime:
        """The current time, timezone-aware."""
        ...  # pragma: no cover — structural signature, never executed


class SystemClock:
    """The real :class:`Clock`: wraps ``datetime.now(UTC)``."""

    def now(self) -> datetime:
        return datetime.now(UTC)
