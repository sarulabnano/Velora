"""The voice Provider domain: synthesizing speech from text.

The provider-agnostic contract (:class:`VoiceProvider`,
:class:`SpeechRequest`, :class:`SpeechResult`) and its first concrete
implementation, :class:`ElevenLabsVoiceProvider`. Future PRs add more
concrete Providers here (Voicebox, XTTS, Piper — see ``docs/VISION.md``)
implementing the same :class:`VoiceProvider` contract, without changing
it.
"""

from __future__ import annotations

from velora.providers.voice._elevenlabs import ElevenLabsVoiceProvider
from velora.providers.voice._protocol import VoiceProvider
from velora.providers.voice._types import SpeechRequest, SpeechResult

__all__ = [
    "ElevenLabsVoiceProvider",
    "SpeechRequest",
    "SpeechResult",
    "VoiceProvider",
]
