"""Tests for velora.providers.voice type shapes."""

from __future__ import annotations

import dataclasses

import pytest

from velora.providers.voice import SpeechRequest, SpeechResult


def test_speech_request_is_frozen() -> None:
    request = SpeechRequest(text="hello")

    with pytest.raises(dataclasses.FrozenInstanceError):
        request.text = "changed"  # type: ignore[misc]


def test_speech_result_is_frozen() -> None:
    result = SpeechResult(audio=b"\x00", audio_format="mp3")

    with pytest.raises(dataclasses.FrozenInstanceError):
        result.audio_format = "wav"  # type: ignore[misc]


def test_speech_result_holds_the_given_audio_bytes_and_format() -> None:
    result = SpeechResult(audio=b"some-bytes", audio_format="mp3")

    assert result.audio == b"some-bytes"
    assert result.audio_format == "mp3"
