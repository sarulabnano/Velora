"""Runtime's own time abstraction.

Runtime never imports ``velora.services`` (Services sits above Runtime
in the dependency layering — architecture.md original §4). This
Protocol is Runtime's own, satisfied structurally by
``velora.services.SystemClock`` — or any object with a matching
``now()`` method — without either package importing the other. See
ADR-0007.
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
    """The real :class:`Clock`: wraps ``datetime.now(UTC)``.

    This is Runtime's default when no ``clock`` is injected — the exact
    behavior Runtime had before this type existed.
    """

    def now(self) -> datetime:
        return datetime.now(UTC)
