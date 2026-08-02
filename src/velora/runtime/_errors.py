"""Runtime error hierarchy.

Named ``VeloraRuntimeError`` — not ``RuntimeError`` — deliberately.
This module is named ``runtime``; an exception named ``RuntimeError``
inside it would collide, by name, with the Python builtin of the same
name. `except RuntimeError` at a call site would then silently catch
both, without the author necessarily noticing which one they meant.
"""

from __future__ import annotations

__all__ = [
    "RuntimeAlreadyStartedError",
    "RuntimeBootstrapError",
    "RuntimeNotRunningError",
    "RuntimeShutdownError",
    "VeloraRuntimeError",
]


class VeloraRuntimeError(Exception):
    """Base class for all errors raised by :mod:`velora.runtime`."""


class RuntimeAlreadyStartedError(VeloraRuntimeError):
    """Raised when :meth:`Runtime.start` is called outside ``NOT_STARTED``.

    A ``Runtime`` instance is single-use. This is raised both when
    starting an already-running instance and when attempting to restart
    one that has already stopped or failed.
    """


class RuntimeNotRunningError(VeloraRuntimeError):
    """Raised when an operation requires state ``RUNNING`` but it isn't.

    Raised by :meth:`Runtime.stop` when the runtime is not running, and
    by :attr:`Runtime.context` when accessed before a successful start.
    """


class RuntimeBootstrapError(VeloraRuntimeError):
    """Raised when a component fails during :meth:`Runtime.start`.

    The triggering exception is always available via ``__cause__``.
    Components already started before the failure are stopped, in
    reverse order, on a best-effort basis before this is raised.
    """


class RuntimeShutdownError(VeloraRuntimeError):
    """Raised when one or more components fail during :meth:`Runtime.stop`.

    All components are given the chance to stop, in reverse start order,
    regardless of earlier failures in the same shutdown sequence. The
    first failure encountered is available via ``__cause__``.
    """
