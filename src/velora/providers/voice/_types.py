"""Typed shapes for the voice Provider domain.

Deliberately provider-agnostic: nothing here mentions ElevenLabs,
Piper, XTTS, or any concrete vendor — same discipline
``text_generation/_types.py`` already established for its domain.

Synchronous and non-streaming only, for now, for the same reason
``text_generation`` is: no consumer with an asynchronous execution
model or a real streaming need exists yet. Both are additive,
non-breaking extensions of :class:`~velora.providers.voice.VoiceProvider`
when they arrive.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["SpeechRequest", "SpeechResult"]


@dataclass(frozen=True, slots=True)
class SpeechRequest:
    """A provider-agnostic request to synthesize speech from text.

    Deliberately minimal: ``text`` is the only field that varies for
    the domain's single real caller today. Voice selection lives on the
    Provider itself (a constructor parameter, e.g. ``voice_id`` on
    :class:`~velora.providers.voice.ElevenLabsVoiceProvider`) — the same
    role ``model`` plays for
    :class:`~velora.providers.text_generation.AnthropicTextGenerationProvider`
    — not here, because no real caller needs to vary voice between
    successive calls to the same Provider yet (ADR-0013). When one does,
    that is the moment to move it onto this type.
    """

    text: str


@dataclass(frozen=True, slots=True)
class SpeechResult:
    """A provider-agnostic result from a speech-synthesis request.

    ``audio_format`` is a plain string, not an enum: with exactly one
    real Provider producing exactly one format (``"mp3"``), a one-member
    enum would model a distinction that doesn't exist yet (ADR-0013).
    """

    audio: bytes
    audio_format: str
