"""The RuntimeEventListener that logs every Runtime lifecycle event."""

from __future__ import annotations

import logging as _stdlib_logging
import sys
from typing import TYPE_CHECKING

from velora.logging._formatting import format_event
from velora.runtime import RuntimeEventKind

if TYPE_CHECKING:
    from typing import TextIO

    from velora.logging._settings import LoggingSettings
    from velora.runtime import RuntimeEvent

__all__ = ["RuntimeEventLogger"]

_DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


class RuntimeEventLogger:
    """Logs every :class:`~velora.runtime.RuntimeEvent` it receives.

    Implements :class:`~velora.runtime.RuntimeEventListener` structurally
    — this class never imports it, and ``velora.runtime`` never imports
    this class. Architecture.md §7: the Runtime never writes logs
    itself; this is the backend that decides how events are recorded.

    Uses ``logging.Logger(name, ...)`` — constructed directly, not
    ``logging.getLogger(name)`` — so each instance is a private logger,
    detached from the standard library's global registry and root
    logger hierarchy. Two ``RuntimeEventLogger`` instances, even with the
    same ``name``, never share state ("No Singletons Globales").

    :meth:`on_runtime_event` does not catch exceptions from the
    underlying standard-library logging calls: per ADR-0004, a listener
    is expected not to raise under normal operation, and a broken output
    stream is not normal operation — it should surface immediately, not
    be silently swallowed.
    """

    def __init__(
        self,
        settings: LoggingSettings,
        *,
        stream: TextIO | None = None,
        name: str = "velora",
    ) -> None:
        self._logger = _stdlib_logging.Logger(name, level=settings.level.to_stdlib_level())
        self._logger.propagate = False
        handler = _stdlib_logging.StreamHandler(stream if stream is not None else sys.stderr)
        handler.setFormatter(_stdlib_logging.Formatter(_DEFAULT_FORMAT))
        self._logger.addHandler(handler)

    def on_runtime_event(self, event: RuntimeEvent) -> None:
        message = format_event(event)
        if event.kind is RuntimeEventKind.FATAL_ERROR:
            self._logger.error(message)
        else:
            self._logger.info(message)
