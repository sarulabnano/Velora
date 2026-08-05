"""VoiceService: the second capability Service (ADR-0014).

``docs/VISION.md``: Services "representan capacidades del sistema... no
representan APIs" — the same principle ADR-0010 already applied to
``NarrationService``, for the ``voice`` domain instead of
``text_generation``. This wraps
:class:`~velora.providers.voice.VoiceProvider` — the caller never knows,
or needs to know, which concrete Provider spoke.

Deliberately thin: it does not decide which voice to use (that lives on
the injected Provider, ADR-0013) or accumulate configuration no real
caller needs yet. Deciding *when* to speak, and how it fits into a
larger pipeline, is business logic that belongs to a future Engine or
Workflow — this Service only knows how to turn text into audio.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from velora.providers.voice import SpeechRequest

if TYPE_CHECKING:
    from velora.providers.voice import SpeechResult, VoiceProvider

__all__ = ["VoiceService"]


class VoiceService:
    """Synthesizes speech via an injected
    :class:`~velora.providers.voice.VoiceProvider`.

    The Provider is a dependency, never constructed internally — this
    Service does not know, and must not know, whether it is talking to
    ElevenLabs, Piper, or anything else.
    """

    def __init__(self, provider: VoiceProvider) -> None:
        self._provider = provider

    def speak(self, text: str) -> SpeechResult:
        """Synthesize speech for ``text``.

        :raises ValueError: ``text`` is empty or only whitespace.
        :raises ~velora.providers.VeloraProviderError: the underlying
            Provider failed — see its own error hierarchy for specifics
            (authentication, rate limiting, connection, or other).
        """
        if not text.strip():
            raise ValueError("text must not be empty.")

        return self._provider.synthesize(SpeechRequest(text=text))
