"""Velora Runtime: bootstrap, lifecycle, and ordered shutdown.

The Runtime is the stable core of Velora (architecture.md §5). It knows
nothing about Configuration, Logging, Services, Providers, Engines,
Workflows, or Extensions — only the contracts exported here:
:class:`LifecycleComponent` (what a component is),
:class:`RuntimeEventListener` (how the Runtime reports what it's doing),
:class:`Clock` and :class:`IdGenerator` (its only two dependencies with
a self-constructed default — see ADR-0007). Every later roadmap phase
depends on this module; this module depends on none of them.

Public surface, deliberately small:
"""

from __future__ import annotations

from velora.runtime._clock import Clock, SystemClock
from velora.runtime._context import RuntimeContext
from velora.runtime._errors import (
    RuntimeAlreadyStartedError,
    RuntimeBootstrapError,
    RuntimeNotRunningError,
    RuntimeShutdownError,
    VeloraRuntimeError,
)
from velora.runtime._events import RuntimeEvent, RuntimeEventKind, RuntimeEventListener
from velora.runtime._id_generator import IdGenerator, UUIDIdGenerator
from velora.runtime._lifecycle import LifecycleComponent
from velora.runtime._runtime import Runtime
from velora.runtime._state import RuntimeState

__all__ = [
    "Clock",
    "IdGenerator",
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
    "SystemClock",
    "UUIDIdGenerator",
    "VeloraRuntimeError",
]
