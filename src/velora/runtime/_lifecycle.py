"""The contract components implement to participate in the Runtime lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from velora.runtime._context import RuntimeContext

__all__ = ["LifecycleComponent"]


@runtime_checkable
class LifecycleComponent(Protocol):
    """A unit the Runtime starts and stops as part of its lifecycle.

    This is the only contract through which the Runtime knows about
    Configuration, Logging, Services, or any component from a later
    roadmap phase. The Runtime never imports those phases directly; it
    only ever depends on this protocol. Components are injected into
    :class:`~velora.runtime.Runtime` by the caller — the Runtime never
    constructs one itself, per the project's Dependency Injection rule.

    ``start`` and ``stop`` are each called exactly once per lifecycle: in
    the order given at construction for ``start``, and in reverse order
    for ``stop``. A component must not perform side effects in its
    constructor; all side effects belong in ``start``.
    """

    @property
    def name(self) -> str:
        """A short, stable, human-readable identifier for this component.

        Used to identify the component in :class:`RuntimeEvent` instances
        and in error messages. Must not change across calls.
        """
        ...  # pragma: no cover — structural signature, never executed

    def start(self, context: RuntimeContext) -> None:
        """Start this component. Raise on failure; never fail silently."""
        ...  # pragma: no cover — structural signature, never executed

    def stop(self, context: RuntimeContext) -> None:
        """Stop this component. Raise on failure; never fail silently."""
        ...  # pragma: no cover — structural signature, never executed
