"""Tests for velora.workflows.story.StoryWorkflow.

Uses real StoryEngine/NarrationAudioEngine/SceneImageEngine (and,
beneath them, real NarrationService/VoiceService/ImageService) with
fake Providers -- the only faked boundary is the actual external call,
same testing philosophy ADR-0011/ADR-0015/ADR-0019 already established
for those Engines' own tests: exercise the real integration all the way
down to the fake external boundary, not a mocked stand-in for an
intermediate layer.
"""

from __future__ import annotations

import pytest

from velora.engines.narration_audio import NarrationAudioEngine
from velora.engines.scene_image import SceneImageEngine
from velora.engines.story import StoryEngine
from velora.engines.subtitle import SubtitleEngine
from velora.engines.timeline import TimelineEngine
from velora.providers import ProviderRequestError
from velora.providers.image import ImageRequest, ImageResult
from velora.providers.text_generation import TextGenerationRequest, TextGenerationResult
from velora.providers.voice import SpeechRequest, SpeechResult
from velora.services.image import ImageService
from velora.services.narration import NarrationService
from velora.services.voice import VoiceService
from velora.workflows.story import StoryWorkflow


class _FakeTextGenerationProvider:
    def __init__(self, text: str) -> None:
        self._text = text
        self.received_requests: list[TextGenerationRequest] = []

    def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
        self.received_requests.append(request)
        return TextGenerationResult(
            text=self._text, stop_reason="end_turn", input_tokens=10, output_tokens=20
        )


class _FakeVoiceProvider:
    def __init__(self) -> None:
        self.received_requests: list[SpeechRequest] = []

    def synthesize(self, request: SpeechRequest) -> SpeechResult:
        self.received_requests.append(request)
        return SpeechResult(audio=request.text.encode(), audio_format="mp3")


class _FakeImageProvider:
    def __init__(self) -> None:
        self.received_requests: list[ImageRequest] = []

    def generate(self, request: ImageRequest) -> ImageResult:
        self.received_requests.append(request)
        return ImageResult(image=request.prompt.encode(), image_format="png")


class _FailingVoiceProvider:
    def synthesize(self, request: SpeechRequest) -> SpeechResult:
        del request
        raise ProviderRequestError("synthesis failed")


class _FailingImageProvider:
    def generate(self, request: ImageRequest) -> ImageResult:
        del request
        raise ProviderRequestError("generation failed")


def _workflow(
    text: str,
) -> tuple[StoryWorkflow, _FakeTextGenerationProvider, _FakeVoiceProvider, _FakeImageProvider]:
    text_provider = _FakeTextGenerationProvider(text)
    voice_provider = _FakeVoiceProvider()
    image_provider = _FakeImageProvider()
    workflow = StoryWorkflow(
        StoryEngine(NarrationService(text_provider)),
        NarrationAudioEngine(VoiceService(voice_provider)),
        SceneImageEngine(ImageService(image_provider)),
        SubtitleEngine(),
        TimelineEngine(),
    )
    return workflow, text_provider, voice_provider, image_provider


def test_run_returns_a_narrated_story_with_the_given_topic() -> None:
    workflow, _, _, _ = _workflow("Some narration.")

    narrated_story = workflow.run("The history of bridges")

    assert narrated_story.story.topic == "The history of bridges"
    assert narrated_story.audio.topic == "The history of bridges"
    assert narrated_story.images.topic == "The history of bridges"


def test_run_divides_narration_into_ordered_scenes() -> None:
    workflow, _, _, _ = _workflow("The city wakes.\n\nThe market opens.\n\nNight falls again.")

    narrated_story = workflow.run("A day in the city")

    assert [scene.text for scene in narrated_story.story.scenes] == [
        "The city wakes.",
        "The market opens.",
        "Night falls again.",
    ]
    assert [scene.index for scene in narrated_story.story.scenes] == [0, 1, 2]


def test_run_synthesizes_audio_for_every_scene_in_order() -> None:
    workflow, _, _, _ = _workflow("The city wakes.\n\nThe market opens.")

    narrated_story = workflow.run("A day in the city")

    assert [s.audio for s in narrated_story.audio.scenes] == [
        b"The city wakes.",
        b"The market opens.",
    ]
    assert [s.index for s in narrated_story.audio.scenes] == [0, 1]


def test_run_illustrates_every_scene_in_order() -> None:
    workflow, _, _, _ = _workflow("The city wakes.\n\nThe market opens.")

    narrated_story = workflow.run("A day in the city")

    assert [s.image for s in narrated_story.images.scenes] == [
        b"The city wakes.",
        b"The market opens.",
    ]
    assert [s.index for s in narrated_story.images.scenes] == [0, 1]


def test_each_built_scenes_text_is_sent_to_the_voice_provider() -> None:
    workflow, _, voice_provider, _ = _workflow("First scene.\n\nSecond scene.")

    workflow.run("A topic")

    assert [r.text for r in voice_provider.received_requests] == [
        "First scene.",
        "Second scene.",
    ]


def test_each_built_scenes_text_is_sent_to_the_image_provider_as_the_prompt() -> None:
    workflow, _, _, image_provider = _workflow("First scene.\n\nSecond scene.")

    workflow.run("A topic")

    assert [r.prompt for r in image_provider.received_requests] == [
        "First scene.",
        "Second scene.",
    ]


def test_run_captions_every_scene_in_order() -> None:
    workflow, _, _, _ = _workflow("The city wakes.\n\nThe market opens.")

    narrated_story = workflow.run("A day in the city")

    assert [s.text for s in narrated_story.subtitles.scenes] == [
        "The city wakes.",
        "The market opens.",
    ]
    assert [s.index for s in narrated_story.subtitles.scenes] == [0, 1]


def test_run_builds_a_timeline_combining_all_four_prior_results() -> None:
    workflow, _, _, _ = _workflow("The city wakes.\n\nThe market opens.")

    narrated_story = workflow.run("A day in the city")

    assert [s.index for s in narrated_story.timeline.scenes] == [0, 1]
    assert [s.text for s in narrated_story.timeline.scenes] == [
        "The city wakes.",
        "The market opens.",
    ]
    first, second = narrated_story.timeline.scenes
    assert first.audio == narrated_story.audio.scenes[0].audio
    assert first.image == narrated_story.images.scenes[0].image
    assert first.start_seconds == narrated_story.subtitles.scenes[0].start_seconds
    assert first.end_seconds == narrated_story.subtitles.scenes[0].end_seconds
    assert second.audio == narrated_story.audio.scenes[1].audio


def test_max_tokens_is_passed_through_to_the_story_engine() -> None:
    workflow, text_provider, _, _ = _workflow("Some narration.")

    workflow.run("A topic", max_tokens=77)

    assert text_provider.received_requests[0].max_tokens == 77


def test_max_tokens_defaults_to_1024() -> None:
    workflow, text_provider, _, _ = _workflow("Some narration.")

    workflow.run("A topic")

    assert text_provider.received_requests[0].max_tokens == 1024


@pytest.mark.parametrize("blank", ["", "   ", "\n\t"])
def test_rejects_empty_topic(blank: str) -> None:
    workflow, text_provider, voice_provider, image_provider = _workflow("Some narration.")

    with pytest.raises(ValueError, match="must not be empty"):
        workflow.run(blank)

    assert text_provider.received_requests == []
    assert voice_provider.received_requests == []
    assert image_provider.received_requests == []


def test_blank_narration_produces_a_narrated_story_with_zero_scenes() -> None:
    workflow, _, voice_provider, image_provider = _workflow("   \n\n  ")

    narrated_story = workflow.run("Nothing to say")

    assert narrated_story.story.scenes == ()
    assert narrated_story.audio.scenes == ()
    assert narrated_story.images.scenes == ()
    assert narrated_story.subtitles.scenes == ()
    assert narrated_story.timeline.scenes == ()
    assert voice_provider.received_requests == []
    assert image_provider.received_requests == []


def test_a_failing_synthesis_propagates_and_returns_no_narrated_story() -> None:
    text_provider = _FakeTextGenerationProvider("First scene.\n\nSecond scene.")
    workflow = StoryWorkflow(
        StoryEngine(NarrationService(text_provider)),
        NarrationAudioEngine(VoiceService(_FailingVoiceProvider())),
        SceneImageEngine(ImageService(_FakeImageProvider())),
        SubtitleEngine(),
        TimelineEngine(),
    )

    with pytest.raises(ProviderRequestError):
        workflow.run("A topic")


def test_a_failing_illustration_propagates_and_returns_no_narrated_story() -> None:
    text_provider = _FakeTextGenerationProvider("First scene.\n\nSecond scene.")
    workflow = StoryWorkflow(
        StoryEngine(NarrationService(text_provider)),
        NarrationAudioEngine(VoiceService(_FakeVoiceProvider())),
        SceneImageEngine(ImageService(_FailingImageProvider())),
        SubtitleEngine(),
        TimelineEngine(),
    )

    with pytest.raises(ProviderRequestError):
        workflow.run("A topic")


def test_works_identically_with_any_conforming_providers() -> None:
    """The architectural point: swap the Providers behind any Engine,
    StoryWorkflow behaves identically -- it never sees a Provider, nor
    even a Service, at all."""

    class _AnotherFakeTextGenerationProvider:
        def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
            del request
            return TextGenerationResult(
                text="A completely different backend narrated this.",
                stop_reason="end_turn",
                input_tokens=1,
                output_tokens=1,
            )

    class _AnotherFakeVoiceProvider:
        def synthesize(self, request: SpeechRequest) -> SpeechResult:
            del request
            return SpeechResult(audio=b"a-completely-different-backend", audio_format="wav")

    class _AnotherFakeImageProvider:
        def generate(self, request: ImageRequest) -> ImageResult:
            del request
            return ImageResult(image=b"a-completely-different-backend", image_format="webp")

    workflow = StoryWorkflow(
        StoryEngine(NarrationService(_AnotherFakeTextGenerationProvider())),
        NarrationAudioEngine(VoiceService(_AnotherFakeVoiceProvider())),
        SceneImageEngine(ImageService(_AnotherFakeImageProvider())),
        SubtitleEngine(),
        TimelineEngine(),
    )

    narrated_story = workflow.run("Anything")

    assert narrated_story.story.scenes[0].text == "A completely different backend narrated this."
    assert narrated_story.audio.scenes[0].audio == b"a-completely-different-backend"
    assert narrated_story.audio.scenes[0].audio_format == "wav"
    assert narrated_story.images.scenes[0].image == b"a-completely-different-backend"
    assert narrated_story.images.scenes[0].image_format == "webp"
    assert (
        narrated_story.subtitles.scenes[0].text == "A completely different backend narrated this."
    )
    assert narrated_story.timeline.scenes[0].audio == b"a-completely-different-backend"
    assert narrated_story.timeline.scenes[0].image_format == "webp"
