"""Velora Runtime: bootstrap, lifecycle, and ordered shutdown.

The Runtime is the stable core of Velora (architecture.md §5). It knows
nothing about Configuration, Logging, Providers, Engines, Workflows, or
Extensions — only the two contracts exported here:
:class:`LifecycleComponent` (what a component is) and
:class:`RuntimeEventListener` (how the Runtime reports what it's doing).
Every later roadmap phase depends on this module; this module depends on
none of them.

Public surface, deliberately small:
"""

from __future__ import annotations

from velora.runtime._context import RuntimeContext
from velora.runtime._errors import (
    RuntimeAlreadyStartedError,
    RuntimeBootstrapError,
    RuntimeNotRunningError,
    RuntimeShutdownError,
    VeloraRuntimeError,
)
from velora.runtime._events import RuntimeEvent, RuntimeEventKind, RuntimeEventListener
from velora.runtime._lifecycle import LifecycleComponent
from velora.runtime._runtime import Runtime
from velora.runtime._state import RuntimeState

__all__ = [
    "LifecycleComponent",
    "Runtime",
    "RuntimeAlreadyStartedError",
    "RuntimeBootstrapError",
    "RuntimeContext",
    "RuntimeEvent",
    "RuntimeEventKind",
    "RuntimeEventListener",
    "RuntimeNotRunningError",
    "RuntimeShutdownError",
    "RuntimeState",
    "VeloraRuntimeError",
]
