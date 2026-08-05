"""Tests for velora.engines.story.StoryEngine.

Uses a real NarrationService, with a fake TextGenerationProvider — the
only faked boundary is the actual external call. This exercises the
real StoryEngine -> NarrationService integration, not a mocked stand-in
for NarrationService itself.
"""

from __future__ import annotations

import pytest

from velora.engines.story import StoryEngine
from velora.providers.text_generation import TextGenerationRequest, TextGenerationResult
from velora.services.narration import NarrationService


class _FakeProvider:
    def __init__(self, text: str) -> None:
        self._text = text
        self.received_requests: list[TextGenerationRequest] = []

    def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
        self.received_requests.append(request)
        return TextGenerationResult(
            text=self._text, stop_reason="end_turn", input_tokens=10, output_tokens=20
        )


def _engine(text: str) -> tuple[StoryEngine, _FakeProvider]:
    provider = _FakeProvider(text)
    engine = StoryEngine(NarrationService(provider))
    return engine, provider


def test_multi_paragraph_narration_becomes_multiple_ordered_scenes() -> None:
    engine, _ = _engine("The city wakes.\n\nThe market opens.\n\nNight falls again.")

    story = engine.build_story("A day in the city")

    assert [scene.text for scene in story.scenes] == [
        "The city wakes.",
        "The market opens.",
        "Night falls again.",
    ]
    assert [scene.index for scene in story.scenes] == [0, 1, 2]


def test_single_paragraph_narration_becomes_one_scene() -> None:
    engine, _ = _engine("A single unbroken narration.")

    story = engine.build_story("Something short")

    assert len(story.scenes) == 1
    assert story.scenes[0].text == "A single unbroken narration."


def test_extra_blank_lines_do_not_produce_empty_scenes() -> None:
    engine, _ = _engine("First.\n\n\n\nSecond.\n\n   \n\nThird.")

    story = engine.build_story("Whitespace stress test")

    assert [scene.text for scene in story.scenes] == ["First.", "Second.", "Third."]


def test_blank_narration_produces_zero_scenes_not_an_error() -> None:
    engine, _ = _engine("   \n\n  ")

    story = engine.build_story("Nothing to say")

    assert story.scenes == ()


def test_story_topic_matches_the_input() -> None:
    engine, _ = _engine("Some narration.")

    story = engine.build_story("The history of bridges")

    assert story.topic == "The history of bridges"


def test_topic_is_embedded_in_the_narration_instructions() -> None:
    engine, provider = _engine("Some narration.")

    engine.build_story("The history of bridges")

    sent_instructions = provider.received_requests[0].messages[0].content
    assert "The history of bridges" in sent_instructions


def test_max_tokens_is_passed_through() -> None:
    engine, provider = _engine("Some narration.")

    engine.build_story("A topic", max_tokens=77)

    assert provider.received_requests[0].max_tokens == 77


def test_max_tokens_defaults_to_1024() -> None:
    engine, provider = _engine("Some narration.")

    engine.build_story("A topic")

    assert provider.received_requests[0].max_tokens == 1024


@pytest.mark.parametrize("blank", ["", "   ", "\n\t"])
def test_rejects_empty_topic(blank: str) -> None:
    engine, provider = _engine("Some narration.")

    with pytest.raises(ValueError, match="must not be empty"):
        engine.build_story(blank)

    assert provider.received_requests == []


def test_works_identically_with_any_conforming_provider() -> None:
    """The architectural point: swap the Provider behind NarrationService,
    StoryEngine behaves identically — it never sees the Provider at all."""

    class _AnotherFakeProvider:
        def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
            del request
            return TextGenerationResult(
                text="A completely different backend narrated this.",
                stop_reason="end_turn",
                input_tokens=1,
                output_tokens=1,
            )

    engine = StoryEngine(NarrationService(_AnotherFakeProvider()))

    story = engine.build_story("Anything")

    assert story.scenes[0].text == "A completely different backend narrated this."
