"""Log level, as understood by the logging backend.

Deliberately a separate type from ``velora.configuration.LogLevel``, not
a shared import. See ADR-0006: Logging sits below Configuration in the
dependency layering (architecture.md original §4), so it must not import
anything from Configuration; the composition root translates between the
two.

``import logging`` below resolves to the Python standard library, not to
this package (``velora.logging``) itself — Python 3 uses absolute
imports by default, and this package is never itself a top-level
``sys.path`` entry. Verified empirically before relying on it.
"""

from __future__ import annotations

import logging as _stdlib_logging
from enum import Enum, unique

__all__ = ["LogLevel"]


@unique
class LogLevel(Enum):
    """A logging severity level, as understood by the logging backend."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    def to_stdlib_level(self) -> int:
        """The equivalent level from the standard library ``logging`` module."""
        return _STDLIB_LEVELS[self]


_STDLIB_LEVELS: dict[LogLevel, int] = {
    LogLevel.DEBUG: _stdlib_logging.DEBUG,
    LogLevel.INFO: _stdlib_logging.INFO,
    LogLevel.WARNING: _stdlib_logging.WARNING,
    LogLevel.ERROR: _stdlib_logging.ERROR,
    LogLevel.CRITICAL: _stdlib_logging.CRITICAL,
}
