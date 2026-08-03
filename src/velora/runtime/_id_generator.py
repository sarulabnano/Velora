"""Runtime's own unique-identifier abstraction.

Same rationale as ``_clock.py``: Runtime never imports
``velora.services``. This Protocol is satisfied structurally by
``velora.services.UUIDIdGenerator`` without any cross-import. See
ADR-0007.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import uuid4

__all__ = ["IdGenerator", "UUIDIdGenerator"]


@runtime_checkable
class IdGenerator(Protocol):
    """A source of new unique identifiers."""

    def new_id(self) -> str:
        """A new, unique identifier."""
        ...  # pragma: no cover — structural signature, never executed


class UUIDIdGenerator:
    """The real :class:`IdGenerator`: wraps ``uuid.uuid4()``.

    This is Runtime's default when no ``id_generator`` is injected — the
    exact behavior Runtime had before this type existed.
    """

    def new_id(self) -> str:
        return str(uuid4())
