"""Tests for velora.services.voice.VoiceService.

Uses a fake VoiceProvider throughout — never ElevenLabsVoiceProvider —
to make the architectural point explicit: VoiceService works
identically regardless of which concrete Provider answers
(docs/VISION.md, ADR-0008).
"""

from __future__ import annotations

import pytest

from velora.providers.voice import SpeechRequest, SpeechResult
from velora.services.voice import VoiceService


class _FakeProvider:
    def __init__(self, result: SpeechResult) -> None:
        self._result = result
        self.received_requests: list[SpeechRequest] = []

    def synthesize(self, request: SpeechRequest) -> SpeechResult:
        self.received_requests.append(request)
        return self._result


def _fake_result(audio: bytes = b"fake-audio") -> SpeechResult:
    return SpeechResult(audio=audio, audio_format="mp3")


def test_speak_returns_the_providers_result() -> None:
    provider = _FakeProvider(_fake_result(b"the-actual-audio"))
    service = VoiceService(provider)

    result = service.speak("Hello there.")

    assert result.audio == b"the-actual-audio"


def test_speak_sends_text_to_the_provider() -> None:
    provider = _FakeProvider(_fake_result())
    service = VoiceService(provider)

    service.speak("Describe a sunrise over the mountains.")

    sent = provider.received_requests[0]
    assert sent.text == "Describe a sunrise over the mountains."


@pytest.mark.parametrize("blank", ["", "   ", "\n\t"])
def test_speak_rejects_empty_text(blank: str) -> None:
    provider = _FakeProvider(_fake_result())
    service = VoiceService(provider)

    with pytest.raises(ValueError, match="must not be empty"):
        service.speak(blank)


def test_speak_does_not_call_the_provider_when_text_is_empty() -> None:
    provider = _FakeProvider(_fake_result())
    service = VoiceService(provider)

    with pytest.raises(ValueError):
        service.speak("")

    assert provider.received_requests == []


def test_service_works_identically_with_any_conforming_provider() -> None:
    """The whole point of the contract: swap the provider, nothing else changes."""

    class _AnotherFakeProvider:
        def synthesize(self, request: SpeechRequest) -> SpeechResult:
            del request
            return _fake_result(b"a-completely-different-backend-answered")

    service = VoiceService(_AnotherFakeProvider())

    result = service.speak("Anything.")

    assert result.audio == b"a-completely-different-backend-answered"
