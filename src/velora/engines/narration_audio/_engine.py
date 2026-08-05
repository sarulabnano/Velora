"""NarrationAudioEngine: synthesizes a Story's scenes into audio.

``docs/VISION.md``'s example Workflow lists "generar voz" right after
"dividir escenas" — this Engine is that step: it turns an already-built
:class:`~velora.engines.story.Story` into a
:class:`~velora.engines.narration_audio.StoryAudio`, synthesizing each
:class:`~velora.engines.story.Scene`'s text via an injected
:class:`~velora.services.voice.VoiceService`.

Scope, deliberate:

- Takes a ``Story``, not a raw topic: the previous Engine already built
  and validated it (ADR-0015) — there is no precondition of this
  Engine's own to check.
- No error aggregation: the first scene that fails to synthesize stops
  the whole operation. No real caller needs "partial story audio" yet.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from velora.engines.narration_audio._types import SceneAudio, StoryAudio

if TYPE_CHECKING:
    from velora.engines.story import Story
    from velora.services.voice import VoiceService

__all__ = ["NarrationAudioEngine"]


class NarrationAudioEngine:
    """Synthesizes a :class:`~velora.engines.story.Story` into
    :class:`~velora.engines.narration_audio.StoryAudio`, via an injected
    :class:`~velora.services.voice.VoiceService`.

    Contains the "how to turn a Story into StoryAudio" orchestration —
    the same kind of decision-making that separates an Engine from the
    Service it depends on (ADR-0008), exactly as
    :class:`~velora.engines.story.StoryEngine` already does for
    ``NarrationService``.
    """

    def __init__(self, voice_service: VoiceService) -> None:
        self._voice_service = voice_service

    def synthesize(self, story: Story) -> StoryAudio:
        """Synthesize audio for every scene in ``story``, in order.

        :raises ~velora.providers.VeloraProviderError: the underlying
            Provider failed while synthesizing some scene — synthesis
            stops at the first failure; no partial result is returned.
        """
        scenes = []
        for scene in story.scenes:
            result = self._voice_service.speak(scene.text)
            scenes.append(
                SceneAudio(index=scene.index, audio=result.audio, audio_format=result.audio_format)
            )
        return StoryAudio(topic=story.topic, scenes=tuple(scenes))
