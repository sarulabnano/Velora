"""Tests for velora.runtime.LifecycleComponent."""

from __future__ import annotations

from datetime import UTC, datetime

from velora.runtime import LifecycleComponent, RuntimeContext


class _Component:
    @property
    def name(self) -> str:
        return "example"

    def start(self, context: RuntimeContext) -> None:
        del context

    def stop(self, context: RuntimeContext) -> None:
        del context


def test_conforming_object_is_recognized_as_lifecycle_component() -> None:
    component = _Component()

    assert isinstance(component, LifecycleComponent)


def test_object_missing_stop_is_not_a_lifecycle_component() -> None:
    class _Incomplete:
        @property
        def name(self) -> str:
            return "incomplete"

        def start(self, context: RuntimeContext) -> None:
            del context

    assert not isinstance(_Incomplete(), LifecycleComponent)


def test_component_receives_the_context_passed_to_it() -> None:
    component = _Component()
    context = RuntimeContext(runtime_id="rid", started_at=datetime.now(UTC))

    component.start(context)
    component.stop(context)
