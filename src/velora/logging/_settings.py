"""Typed configuration for the logging backend."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from velora.logging._level import LogLevel

__all__ = ["LoggingSettings"]


@dataclass(frozen=True, slots=True)
class LoggingSettings:
    """Configuration for :class:`~velora.logging.RuntimeEventLogger`.

    Constructed explicitly by the composition root from an already-typed
    :class:`LogLevel` — never from a raw source. See ADR-0006.
    """

    level: LogLevel
