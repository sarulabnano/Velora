"""Tests for velora.workflows.story.StoryWorkflow.

Uses a real StoryEngine (and, beneath it, a real NarrationService) with
a fake TextGenerationProvider — the only faked boundary is the actual
external call, same testing philosophy ADR-0011 already established for
StoryEngine's own tests: exercise the real integration all the way down
to the fake external boundary, not a mocked stand-in for an intermediate
layer.
"""

from __future__ import annotations

import pytest

from velora.engines.story import StoryEngine
from velora.providers.text_generation import TextGenerationRequest, TextGenerationResult
from velora.services.narration import NarrationService
from velora.workflows.story import StoryWorkflow


class _FakeProvider:
    def __init__(self, text: str) -> None:
        self._text = text
        self.received_requests: list[TextGenerationRequest] = []

    def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
        self.received_requests.append(request)
        return TextGenerationResult(
            text=self._text, stop_reason="end_turn", input_tokens=10, output_tokens=20
        )


def _workflow(text: str) -> tuple[StoryWorkflow, _FakeProvider]:
    provider = _FakeProvider(text)
    workflow = StoryWorkflow(StoryEngine(NarrationService(provider)))
    return workflow, provider


def test_run_returns_a_story_with_the_given_topic() -> None:
    workflow, _ = _workflow("Some narration.")

    story = workflow.run("The history of bridges")

    assert story.topic == "The history of bridges"


def test_run_divides_narration_into_ordered_scenes() -> None:
    workflow, _ = _workflow("The city wakes.\n\nThe market opens.\n\nNight falls again.")

    story = workflow.run("A day in the city")

    assert [scene.text for scene in story.scenes] == [
        "The city wakes.",
        "The market opens.",
        "Night falls again.",
    ]
    assert [scene.index for scene in story.scenes] == [0, 1, 2]


def test_max_tokens_is_passed_through_to_the_engine() -> None:
    workflow, provider = _workflow("Some narration.")

    workflow.run("A topic", max_tokens=77)

    assert provider.received_requests[0].max_tokens == 77


def test_max_tokens_defaults_to_1024() -> None:
    workflow, provider = _workflow("Some narration.")

    workflow.run("A topic")

    assert provider.received_requests[0].max_tokens == 1024


@pytest.mark.parametrize("blank", ["", "   ", "\n\t"])
def test_rejects_empty_topic(blank: str) -> None:
    workflow, provider = _workflow("Some narration.")

    with pytest.raises(ValueError, match="must not be empty"):
        workflow.run(blank)

    assert provider.received_requests == []


def test_blank_narration_produces_a_story_with_zero_scenes() -> None:
    workflow, _ = _workflow("   \n\n  ")

    story = workflow.run("Nothing to say")

    assert story.scenes == ()


def test_works_identically_with_any_conforming_provider() -> None:
    """The architectural point: swap the Provider behind NarrationService
    and StoryEngine, StoryWorkflow behaves identically — it never sees
    the Provider, nor even the NarrationService, at all."""

    class _AnotherFakeProvider:
        def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
            del request
            return TextGenerationResult(
                text="A completely different backend narrated this.",
                stop_reason="end_turn",
                input_tokens=1,
                output_tokens=1,
            )

    workflow = StoryWorkflow(StoryEngine(NarrationService(_AnotherFakeProvider())))

    story = workflow.run("Anything")

    assert story.scenes[0].text == "A completely different backend narrated this."
