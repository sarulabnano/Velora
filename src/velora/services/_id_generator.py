"""A Service abstracting "generate a new unique identifier".

Same rationale as ``_clock.py``: no import of ``velora.runtime``,
structural compatibility with ``velora.runtime.IdGenerator`` by shape
alone. See ADR-0007.
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
    """The real :class:`IdGenerator`: wraps ``uuid.uuid4()``."""

    def new_id(self) -> str:
        return str(uuid4())
