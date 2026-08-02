"""Runtime event model.

The Runtime never writes logs directly (architecture.md §7): it emits
``RuntimeEvent`` instances to injected listeners, and a listener
decides how — or whether — to record them. The Logging phase will
provide the first real listener; until then, listeners are optional and
supplied by whatever code constructs the ``Runtime``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique
from typing import Protocol, runtime_checkable

__all__ = ["RuntimeEvent", "RuntimeEventKind", "RuntimeEventListener"]


@unique
class RuntimeEventKind(Enum):
    """The kind of a :class:`RuntimeEvent`.

    New kinds may be added in future PRs without breaking existing
    listeners: ``RuntimeEvent`` itself never changes shape, so a listener
    written today keeps working unmodified against a kind it doesn't
    recognize (it simply won't have a branch for it).
    """

    BOOTSTRAP_STARTING = "bootstrap_starting"
    BOOTSTRAP_COMPLETED = "bootstrap_completed"
    COMPONENT_STARTING = "component_starting"
    COMPONENT_STARTED = "component_started"
    COMPONENT_STOPPING = "component_stopping"
    COMPONENT_STOPPED = "component_stopped"
    SHUTDOWN_STARTING = "shutdown_starting"
    SHUTDOWN_COMPLETED = "shutdown_completed"
    FATAL_ERROR = "fatal_error"


@dataclass(frozen=True, slots=True)
class RuntimeEvent:
    """A single occurrence in the Runtime's lifecycle.

    ``component_name`` is set for component-scoped kinds
    (``COMPONENT_*``) and unset for runtime-scoped kinds
    (``BOOTSTRAP_*``, ``SHUTDOWN_*``). ``error`` is set only for
    ``FATAL_ERROR``.
    """

    kind: RuntimeEventKind
    component_name: str | None = None
    error: BaseException | None = None


@runtime_checkable
class RuntimeEventListener(Protocol):
    """The contract a Runtime event subscriber implements.

    The Runtime calls ``on_runtime_event`` synchronously, once per event,
    in emission order. A listener that raises interrupts the Runtime
    immediately: the Runtime does not catch listener exceptions, because
    a listener is expected to be a well-behaved observer, not a source of
    control flow. See ADR-0004.
    """

    def on_runtime_event(self, event: RuntimeEvent) -> None:
        """Handle one runtime event. Must not raise under normal operation."""
        ...  # pragma: no cover — structural signature, never executed
