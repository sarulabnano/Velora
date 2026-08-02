"""Velora Logging: the backend that decides how Runtime events are recorded.

architecture.md original §7: "El Runtime nunca escribe logs directamente.
El Runtime emite eventos. El Logging decide cómo registrarlos." This
package never imports ``velora.configuration`` (ADR-0006) and
``velora.runtime`` never imports this package (ADR-0004/ADR-0005): the
composition root (``velora.cli``) is the only place that wires them
together.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from velora.logging._level import LogLevel
from velora.logging._listener import RuntimeEventLogger
from velora.logging._settings import LoggingSettings

if TYPE_CHECKING:
    from typing import TextIO

__all__ = ["LogLevel", "LoggingSettings", "RuntimeEventLogger", "configure_logging"]


def configure_logging(
    settings: LoggingSettings,
    *,
    stream: TextIO | None = None,
    name: str = "velora",
) -> RuntimeEventLogger:
    """Build a :class:`RuntimeEventLogger` from ``settings``.

    ``stream`` defaults to ``sys.stderr`` — read at call time, so it
    respects any stream substitution (for example, ``pytest``'s
    ``capsys``) already in place when this is called.
    """
    return RuntimeEventLogger(settings, stream=stream, name=name)
