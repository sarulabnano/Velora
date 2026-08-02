"""Tests for velora.runtime.Runtime."""

from __future__ import annotations

import pytest

from velora.runtime import (
    Runtime,
    RuntimeAlreadyStartedError,
    RuntimeBootstrapError,
    RuntimeContext,
    RuntimeEvent,
    RuntimeEventKind,
    RuntimeNotRunningError,
    RuntimeShutdownError,
    RuntimeState,
)


class _RecordingComponent:
    """A LifecycleComponent that records what happened to it."""

    def __init__(
        self,
        name: str,
        *,
        fail_on_start: bool = False,
        fail_on_stop: bool = False,
    ) -> None:
        self._name = name
        self._fail_on_start = fail_on_start
        self._fail_on_stop = fail_on_stop
        self.started_with: RuntimeContext | None = None
        self.stopped_with: RuntimeContext | None = None

    @property
    def name(self) -> str:
        return self._name

    def start(self, context: RuntimeContext) -> None:
        if self._fail_on_start:
            raise ValueError(f"{self._name} refuses to start")
        self.started_with = context

    def stop(self, context: RuntimeContext) -> None:
        if self._fail_on_stop:
            raise ValueError(f"{self._name} refuses to stop")
        self.stopped_with = context


class _RecordingListener:
    def __init__(self) -> None:
        self.events: list[RuntimeEvent] = []

    def on_runtime_event(self, event: RuntimeEvent) -> None:
        self.events.append(event)

    def kinds(self) -> list[RuntimeEventKind]:
        return [event.kind for event in self.events]


class _RaisingListener:
    def on_runtime_event(self, event: RuntimeEvent) -> None:
        raise ValueError("listener is broken")


# --- basic lifecycle ---------------------------------------------------


def test_initial_state_is_not_started() -> None:
    runtime = Runtime()

    assert runtime.state is RuntimeState.NOT_STARTED


def test_context_raises_before_start() -> None:
    runtime = Runtime()

    with pytest.raises(RuntimeNotRunningError):
        _ = runtime.context


def test_start_with_no_components_reaches_running() -> None:
    runtime = Runtime()

    runtime.start()

    assert runtime.state is RuntimeState.RUNNING
    assert runtime.context.runtime_id


def test_stop_after_start_reaches_stopped() -> None:
    runtime = Runtime()
    runtime.start()

    runtime.stop()

    assert runtime.state is RuntimeState.STOPPED


def test_components_are_started_in_order_and_receive_context() -> None:
    first = _RecordingComponent("first")
    second = _RecordingComponent("second")
    runtime = Runtime(components=[first, second])

    runtime.start()

    assert first.started_with is runtime.context
    assert second.started_with is runtime.context


def test_components_are_stopped_in_reverse_order() -> None:
    stop_order: list[str] = []

    class _Tracking(_RecordingComponent):
        def stop(self, context: RuntimeContext) -> None:
            stop_order.append(self.name)
            super().stop(context)

    first = _Tracking("first")
    second = _Tracking("second")
    runtime = Runtime(components=[first, second])
    runtime.start()

    runtime.stop()

    assert stop_order == ["second", "first"]
    assert first.stopped_with is not None
    assert second.stopped_with is not None


# --- invalid transitions -------------------------------------------------


def test_start_twice_raises() -> None:
    runtime = Runtime()
    runtime.start()

    with pytest.raises(RuntimeAlreadyStartedError):
        runtime.start()


def test_start_after_stop_raises() -> None:
    runtime = Runtime()
    runtime.start()
    runtime.stop()

    with pytest.raises(RuntimeAlreadyStartedError):
        runtime.start()


def test_stop_before_start_raises() -> None:
    runtime = Runtime()

    with pytest.raises(RuntimeNotRunningError):
        runtime.stop()


def test_stop_twice_raises() -> None:
    runtime = Runtime()
    runtime.start()
    runtime.stop()

    with pytest.raises(RuntimeNotRunningError):
        runtime.stop()


# --- bootstrap failure and unwind ----------------------------------------


def test_failing_component_raises_bootstrap_error() -> None:
    runtime = Runtime(components=[_RecordingComponent("bad", fail_on_start=True)])

    with pytest.raises(RuntimeBootstrapError) as exc_info:
        runtime.start()

    assert isinstance(exc_info.value.__cause__, ValueError)
    assert runtime.state is RuntimeState.FAILED


def test_components_started_before_failure_are_unwound() -> None:
    good = _RecordingComponent("good")
    bad = _RecordingComponent("bad", fail_on_start=True)
    runtime = Runtime(components=[good, bad])

    with pytest.raises(RuntimeBootstrapError):
        runtime.start()

    assert good.started_with is not None
    assert good.stopped_with is not None


def test_unwind_failure_does_not_mask_original_bootstrap_error() -> None:
    flaky = _RecordingComponent("flaky", fail_on_stop=True)
    bad = _RecordingComponent("bad", fail_on_start=True)
    runtime = Runtime(components=[flaky, bad])

    with pytest.raises(RuntimeBootstrapError) as exc_info:
        runtime.start()

    assert isinstance(exc_info.value.__cause__, ValueError)
    assert str(exc_info.value.__cause__) == "bad refuses to start"


# --- shutdown failure ------------------------------------------------------


def test_failing_component_on_stop_raises_shutdown_error() -> None:
    runtime = Runtime(components=[_RecordingComponent("bad", fail_on_stop=True)])
    runtime.start()

    with pytest.raises(RuntimeShutdownError):
        runtime.stop()

    assert runtime.state is RuntimeState.FAILED


def test_shutdown_continues_past_a_failing_component() -> None:
    first = _RecordingComponent("first")
    failing = _RecordingComponent("failing", fail_on_stop=True)
    runtime = Runtime(components=[first, failing])
    runtime.start()

    with pytest.raises(RuntimeShutdownError):
        runtime.stop()

    # `first` started before `failing`, so it is stopped after it (reverse
    # order) — it must still be stopped despite `failing`'s exception.
    assert first.stopped_with is not None


# --- events -----------------------------------------------------------------


def test_successful_lifecycle_emits_expected_event_sequence() -> None:
    listener = _RecordingListener()
    runtime = Runtime(components=[_RecordingComponent("only")], listeners=[listener])

    runtime.start()
    runtime.stop()

    assert listener.kinds() == [
        RuntimeEventKind.BOOTSTRAP_STARTING,
        RuntimeEventKind.COMPONENT_STARTING,
        RuntimeEventKind.COMPONENT_STARTED,
        RuntimeEventKind.BOOTSTRAP_COMPLETED,
        RuntimeEventKind.SHUTDOWN_STARTING,
        RuntimeEventKind.COMPONENT_STOPPING,
        RuntimeEventKind.COMPONENT_STOPPED,
        RuntimeEventKind.SHUTDOWN_COMPLETED,
    ]


def test_bootstrap_failure_emits_fatal_error_with_component_and_exception() -> None:
    listener = _RecordingListener()
    error_component = _RecordingComponent("bad", fail_on_start=True)
    runtime = Runtime(components=[error_component], listeners=[listener])

    with pytest.raises(RuntimeBootstrapError):
        runtime.start()

    fatal_events = [e for e in listener.events if e.kind is RuntimeEventKind.FATAL_ERROR]
    assert len(fatal_events) == 1
    assert fatal_events[0].component_name == "bad"
    assert isinstance(fatal_events[0].error, ValueError)


def test_listener_exception_propagates_immediately() -> None:
    runtime = Runtime(listeners=[_RaisingListener()])

    with pytest.raises(ValueError, match="listener is broken"):
        runtime.start()


# --- context manager ---------------------------------------------------------


def test_context_manager_starts_and_stops() -> None:
    runtime = Runtime()

    with runtime as entered:
        assert entered is runtime
        state_while_running: RuntimeState = runtime.state
        assert state_while_running is RuntimeState.RUNNING

    state_after_exit: RuntimeState = runtime.state
    assert state_after_exit is RuntimeState.STOPPED


def test_context_manager_stops_on_exception_from_body() -> None:
    runtime = Runtime()

    with pytest.raises(ValueError, match="body failed"), runtime:
        raise ValueError("body failed")

    assert runtime.state is RuntimeState.STOPPED


def test_context_manager_does_not_double_stop_if_body_already_stopped() -> None:
    runtime = Runtime()

    with runtime:
        runtime.stop()
        assert runtime.state is RuntimeState.STOPPED

    # __exit__ must not call stop() again on an already-stopped runtime.
    assert runtime.state is RuntimeState.STOPPED


def test_context_manager_propagates_start_failure() -> None:
    runtime = Runtime(components=[_RecordingComponent("bad", fail_on_start=True)])

    with pytest.raises(RuntimeBootstrapError), runtime:
        pytest.fail("body must not run when start() fails")

    assert runtime.state is RuntimeState.FAILED
