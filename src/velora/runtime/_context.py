"""Runtime execution context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

__all__ = ["RuntimeContext"]


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    """Immutable metadata describing one execution of the Runtime.

    A new ``RuntimeContext`` is created each time :meth:`Runtime.start`
    succeeds in beginning a bootstrap sequence. It is passed to every
    :class:`~velora.runtime.LifecycleComponent` so components can
    correlate their own behavior with a specific runtime execution
    (for example, in structured log lines once Logging exists).
    """

    runtime_id: str
    started_at: datetime
