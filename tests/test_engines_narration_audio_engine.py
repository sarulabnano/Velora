"""Tests for velora.engines.narration_audio.NarrationAudioEngine.

Uses a real VoiceService, with a fake VoiceProvider — the only faked
boundary is the actual external call. This exercises the real
NarrationAudioEngine -> VoiceService integration, not a mocked
stand-in for VoiceService itself.
"""

from __future__ import annotations

import pytest

from velora.engines.narration_audio import NarrationAudioEngine
from velora.engines.story import Scene, Story
from velora.providers import ProviderRequestError
from velora.providers.voice import SpeechRequest, SpeechResult
from velora.services.voice import VoiceService


class _FakeProvider:
    def __init__(self) -> None:
        self.received_requests: list[SpeechRequest] = []

    def synthesize(self, request: SpeechRequest) -> SpeechResult:
        self.received_requests.append(request)
        audio = request.text.encode()
        return SpeechResult(audio=audio, audio_format="mp3")


class _FailingProvider:
    def synthesize(self, request: SpeechRequest) -> SpeechResult:
        del request
        raise ProviderRequestError("synthesis failed")


def _engine() -> tuple[NarrationAudioEngine, _FakeProvider]:
    provider = _FakeProvider()
    engine = NarrationAudioEngine(VoiceService(provider))
    return engine, provider


def test_synthesizes_audio_for_every_scene_in_order() -> None:
    engine, _ = _engine()
    story = Story(
        topic="A day in the city",
        scenes=(
            Scene(index=0, text="The city wakes."),
            Scene(index=1, text="The market opens."),
        ),
    )

    story_audio = engine.synthesize(story)

    assert [s.audio for s in story_audio.scenes] == [b"The city wakes.", b"The market opens."]
    assert [s.index for s in story_audio.scenes] == [0, 1]
    assert [s.audio_format for s in story_audio.scenes] == ["mp3", "mp3"]


def test_topic_is_carried_over_from_the_story() -> None:
    engine, _ = _engine()
    story = Story(topic="The history of bridges", scenes=())

    story_audio = engine.synthesize(story)

    assert story_audio.topic == "The history of bridges"


def test_story_with_zero_scenes_produces_zero_scene_audio_not_an_error() -> None:
    engine, provider = _engine()
    story = Story(topic="Nothing to say", scenes=())

    story_audio = engine.synthesize(story)

    assert story_audio.scenes == ()
    assert provider.received_requests == []


def test_each_scenes_text_is_sent_to_the_voice_service() -> None:
    engine, provider = _engine()
    story = Story(
        topic="A day in the city",
        scenes=(Scene(index=0, text="First scene."), Scene(index=1, text="Second scene.")),
    )

    engine.synthesize(story)

    assert [r.text for r in provider.received_requests] == ["First scene.", "Second scene."]


def test_a_failing_scene_stops_synthesis_and_propagates() -> None:
    engine = NarrationAudioEngine(VoiceService(_FailingProvider()))
    story = Story(
        topic="A day in the city",
        scenes=(Scene(index=0, text="First scene."), Scene(index=1, text="Second scene.")),
    )

    with pytest.raises(ProviderRequestError):
        engine.synthesize(story)


def test_works_identically_with_any_conforming_provider() -> None:
    """The architectural point: swap the Provider behind VoiceService,
    NarrationAudioEngine behaves identically — it never sees the
    Provider at all."""

    class _AnotherFakeProvider:
        def synthesize(self, request: SpeechRequest) -> SpeechResult:
            del request
            return SpeechResult(audio=b"a-completely-different-backend", audio_format="wav")

    engine = NarrationAudioEngine(VoiceService(_AnotherFakeProvider()))
    story = Story(topic="Anything", scenes=(Scene(index=0, text="Hi"),))

    story_audio = engine.synthesize(story)

    assert story_audio.scenes[0].audio == b"a-completely-different-backend"
    assert story_audio.scenes[0].audio_format == "wav"
