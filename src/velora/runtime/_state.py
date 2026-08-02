"""Runtime lifecycle state."""

from __future__ import annotations

from enum import Enum, unique

__all__ = ["RuntimeState"]


@unique
class RuntimeState(Enum):
    """The lifecycle state of a :class:`velora.runtime.Runtime` instance.

    Valid transitions::

        NOT_STARTED -> STARTING -> RUNNING -> STOPPING -> STOPPED
        STARTING    -> FAILED   (a component failed to start)
        STOPPING    -> FAILED   (a component failed to stop)

    A ``Runtime`` instance is single-use: there is no transition back to
    ``NOT_STARTED`` from any other state. Restarting requires a new
    ``Runtime`` instance.
    """

    NOT_STARTED = "not_started"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
