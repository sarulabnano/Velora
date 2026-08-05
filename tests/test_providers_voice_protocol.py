"""Tests for velora.providers.voice.VoiceProvider."""

from __future__ import annotations

from velora.providers.voice import SpeechRequest, SpeechResult, VoiceProvider


class _FakeProvider:
    def synthesize(self, request: SpeechRequest) -> SpeechResult:
        del request
        return SpeechResult(audio=b"fake-audio", audio_format="mp3")


def test_conforming_object_is_recognized_as_a_voice_provider() -> None:
    assert isinstance(_FakeProvider(), VoiceProvider)


def test_object_without_synthesize_is_not_a_voice_provider() -> None:
    assert not isinstance(object(), VoiceProvider)


def test_fake_provider_is_directly_callable() -> None:
    provider = _FakeProvider()
    request = SpeechRequest(text="hi")

    result = provider.synthesize(request)

    assert result.audio == b"fake-audio"
