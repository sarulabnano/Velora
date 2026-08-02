"""Log level, as a configuration value.

This is a Configuration-owned type: the *name* of the level a process
should log at, resolved from a raw string like any other setting.
:mod:`velora.logging` defines its own, independent ``LogLevel`` — see
ADR-0006 for why the two are not the same type.
"""

from __future__ import annotations

from enum import Enum, unique

__all__ = ["LogLevel"]


@unique
class LogLevel(Enum):
    """A logging severity level, as a configuration value."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
