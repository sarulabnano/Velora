"""The Runtime: bootstrap, lifecycle, and ordered shutdown of components."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from velora.runtime._context import RuntimeContext
from velora.runtime._errors import (
    RuntimeAlreadyStartedError,
    RuntimeBootstrapError,
    RuntimeNotRunningError,
    RuntimeShutdownError,
)
from velora.runtime._events import RuntimeEvent, RuntimeEventKind, RuntimeEventListener
from velora.runtime._state import RuntimeState

if TYPE_CHECKING:
    from collections.abc import Sequence
    from types import TracebackType

    from velora.runtime._lifecycle import LifecycleComponent

__all__ = ["Runtime"]


class Runtime:
    """The stable core of Velora: bootstrap, lifecycle, ordered shutdown.

    The Runtime knows nothing about Configuration, Logging, Providers,
    Engines, Workflows, or any other later-phase concept. It only knows
    two contracts, both supplied by the caller through dependency
    injection — never constructed internally:

    - ``components``: objects implementing
      :class:`~velora.runtime.LifecycleComponent`, started in the given
      order and stopped in reverse order.
    - ``listeners``: objects implementing
      :class:`~velora.runtime.RuntimeEventListener`, notified of every
      lifecycle event. The Runtime never writes logs itself; a listener
      decides what, if anything, to do with an event.

    A ``Runtime`` instance is single-use: ``NOT_STARTED -> STARTING ->
    RUNNING -> STOPPING -> STOPPED``, with no transition back to
    ``NOT_STARTED``. Construct a new instance to run again.

    This implementation is not thread-safe. Concurrent calls to
    :meth:`start` or :meth:`stop` on the same instance, from multiple
    threads, are unsupported and their outcome is undefined.
    """

    def __init__(
        self,
        components: Sequence[LifecycleComponent] = (),
        listeners: Sequence[RuntimeEventListener] = (),
    ) -> None:
        self._components: tuple[LifecycleComponent, ...] = tuple(components)
        self._listeners: tuple[RuntimeEventListener, ...] = tuple(listeners)
        self._state: RuntimeState = RuntimeState.NOT_STARTED
        self._context: RuntimeContext | None = None
        self._started_components: list[LifecycleComponent] = []

    @property
    def state(self) -> RuntimeState:
        """The current lifecycle state."""
        return self._state

    @property
    def context(self) -> RuntimeContext:
        """The execution context of the current run.

        :raises RuntimeNotRunningError: if the Runtime has not completed
            a successful :meth:`start`.
        """
        if self._context is None:
            raise RuntimeNotRunningError(
                "Runtime has no execution context before a successful start()."
            )
        return self._context

    def start(self) -> None:
        """Run bootstrap: start every component, in order.

        On success, transitions to ``RUNNING``. On failure, components
        already started are stopped, in reverse order, on a best-effort
        basis, then :class:`RuntimeBootstrapError` is raised with the
        triggering exception as its cause.

        :raises RuntimeAlreadyStartedError: if not in state ``NOT_STARTED``.
        :raises RuntimeBootstrapError: if a component fails to start.
        """
        if self._state is not RuntimeState.NOT_STARTED:
            raise RuntimeAlreadyStartedError(
                f"Runtime.start() requires state NOT_STARTED, got {self._state}."
            )

        self._state = RuntimeState.STARTING
        self._context = RuntimeContext(runtime_id=str(uuid4()), started_at=datetime.now(UTC))
        self._emit(RuntimeEvent(kind=RuntimeEventKind.BOOTSTRAP_STARTING))

        for component in self._components:
            self._emit(
                RuntimeEvent(
                    kind=RuntimeEventKind.COMPONENT_STARTING,
                    component_name=component.name,
                )
            )
            try:
                component.start(self._context)
            except Exception as exc:
                self._state = RuntimeState.FAILED
                self._emit(
                    RuntimeEvent(
                        kind=RuntimeEventKind.FATAL_ERROR,
                        component_name=component.name,
                        error=exc,
                    )
                )
                self._unwind_after_bootstrap_failure()
                raise RuntimeBootstrapError(
                    f"Component '{component.name}' failed to start."
                ) from exc

            self._started_components.append(component)
            self._emit(
                RuntimeEvent(
                    kind=RuntimeEventKind.COMPONENT_STARTED,
                    component_name=component.name,
                )
            )

        self._state = RuntimeState.RUNNING
        self._emit(RuntimeEvent(kind=RuntimeEventKind.BOOTSTRAP_COMPLETED))

    def stop(self) -> None:
        """Stop every started component, in reverse start order.

        Every started component is given the chance to stop, even if an
        earlier one failed in the same call: shutdown is best-effort and
        exhaustive, not abort-on-first-failure. On success, transitions
        to ``STOPPED``. If any component failed, transitions to
        ``FAILED`` and raises :class:`RuntimeShutdownError` with the
        first failure as its cause.

        :raises RuntimeNotRunningError: if not in state ``RUNNING``.
        :raises RuntimeShutdownError: if one or more components fail to stop.
        """
        if self._state is not RuntimeState.RUNNING:
            raise RuntimeNotRunningError(
                f"Runtime.stop() requires state RUNNING, got {self._state}."
            )

        self._state = RuntimeState.STOPPING
        self._emit(RuntimeEvent(kind=RuntimeEventKind.SHUTDOWN_STARTING))

        failures: list[tuple[str, BaseException]] = []
        for component in reversed(self._started_components):
            failures.extend(self._stop_one(component))
        self._started_components.clear()

        if failures:
            self._state = RuntimeState.FAILED
            failed_names = [name for name, _ in failures]
            raise RuntimeShutdownError(
                f"{len(failures)} component(s) failed during shutdown: {failed_names}."
            ) from failures[0][1]

        self._state = RuntimeState.STOPPED
        self._emit(RuntimeEvent(kind=RuntimeEventKind.SHUTDOWN_COMPLETED))

    def _stop_one(self, component: LifecycleComponent) -> list[tuple[str, BaseException]]:
        """Stop a single component, emitting events. Never raises."""
        assert self._context is not None  # invariant: always set by start() before this runs
        self._emit(
            RuntimeEvent(kind=RuntimeEventKind.COMPONENT_STOPPING, component_name=component.name)
        )
        try:
            component.stop(self._context)
        except Exception as exc:
            self._emit(
                RuntimeEvent(
                    kind=RuntimeEventKind.FATAL_ERROR,
                    component_name=component.name,
                    error=exc,
                )
            )
            return [(component.name, exc)]

        self._emit(
            RuntimeEvent(kind=RuntimeEventKind.COMPONENT_STOPPED, component_name=component.name)
        )
        return []

    def _unwind_after_bootstrap_failure(self) -> None:
        """Best-effort reverse-order stop of components started so far.

        Failures here are emitted as ``FATAL_ERROR`` events but never
        raised: the caller of :meth:`start` will already receive
        :class:`RuntimeBootstrapError` for the original failure, and that
        is the exception this call is unwinding from.
        """
        for component in reversed(self._started_components):
            self._stop_one(component)
        self._started_components.clear()

    def _emit(self, event: RuntimeEvent) -> None:
        for listener in self._listeners:
            listener.on_runtime_event(event)

    def __enter__(self) -> Runtime:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._state is RuntimeState.RUNNING:
            self.stop()
