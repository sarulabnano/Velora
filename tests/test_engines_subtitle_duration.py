"""Tests for velora.engines.subtitle.measure_duration_seconds."""

from __future__ import annotations

import io
import wave

import pytest

from velora.engines.subtitle import measure_duration_seconds


def _wav_bytes(*, seconds: float, sample_rate: int = 8000) -> bytes:
    frame_count = round(seconds * sample_rate)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate)
        writer.writeframes(b"\x00\x00" * frame_count)
    return buffer.getvalue()


def test_measures_the_exact_duration_of_real_audio() -> None:
    duration = measure_duration_seconds(_wav_bytes(seconds=3.0))

    assert duration == pytest.approx(3.0, abs=0.01)


def test_measures_a_fractional_duration() -> None:
    duration = measure_duration_seconds(_wav_bytes(seconds=1.25))

    assert duration == pytest.approx(1.25, abs=0.01)


def test_returns_none_for_bytes_that_are_not_audio() -> None:
    assert measure_duration_seconds(b"this is not an audio file") is None


def test_returns_none_for_empty_bytes() -> None:
    assert measure_duration_seconds(b"") is None


def test_returns_none_when_mutagen_itself_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """mutagen mostly returns None for unparseable input (see the tests
    above), but its own exception surface for malformed containers isn't
    narrow or fully documented -- this exercises that any exception,
    not just a clean None, is handled the same way."""
    import mutagen

    def _raise(*args: object, **kwargs: object) -> None:
        raise ValueError("simulated mutagen parsing failure")

    monkeypatch.setattr(mutagen, "File", _raise)

    assert measure_duration_seconds(b"irrelevant") is None
