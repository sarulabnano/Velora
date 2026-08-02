"""Turning a RuntimeEvent into a human-readable message."""

from __future__ import annotations

from typing import TYPE_CHECKING, assert_never

from velora.runtime import RuntimeEventKind

if TYPE_CHECKING:
    from velora.runtime import RuntimeEvent

__all__ = ["format_event"]


def format_event(event: RuntimeEvent) -> str:
    """Render ``event`` as a single-line, human-readable message.

    Exhaustive over :class:`~velora.runtime.RuntimeEventKind`: the
    ``case _: assert_never(...)`` branch means mypy — and a test — fail
    if a future PR adds a new kind here without updating this function.
    That is a deliberate integration guardrail, not something reachable
    in normal operation with today's ``RuntimeEventKind``.
    """
    match event.kind:
        case RuntimeEventKind.BOOTSTRAP_STARTING:
            return "runtime bootstrap starting"
        case RuntimeEventKind.BOOTSTRAP_COMPLETED:
            return "runtime bootstrap completed"
        case RuntimeEventKind.COMPONENT_STARTING:
            return f"component '{event.component_name}' starting"
        case RuntimeEventKind.COMPONENT_STARTED:
            return f"component '{event.component_name}' started"
        case RuntimeEventKind.COMPONENT_STOPPING:
            return f"component '{event.component_name}' stopping"
        case RuntimeEventKind.COMPONENT_STOPPED:
            return f"component '{event.component_name}' stopped"
        case RuntimeEventKind.SHUTDOWN_STARTING:
            return "runtime shutdown starting"
        case RuntimeEventKind.SHUTDOWN_COMPLETED:
            return "runtime shutdown completed"
        case RuntimeEventKind.FATAL_ERROR:
            where = f" in component '{event.component_name}'" if event.component_name else ""
            return f"fatal error{where}: {event.error}"
        case _:  # pragma: no cover — exhaustiveness guardrail, unreachable today
            assert_never(event.kind)
