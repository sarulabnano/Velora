"""StoryWorkflow: orchestrates the Engines needed to turn a topic into a
narrated, synthesized, illustrated, captioned Story.

``docs/VISION.md``: "Los Workflows conectan todos los motores." Through
PR-012 that was exactly one motor -- ``StoryEngine``. Since PR-013
(ADR-0016), ``NarrationAudioEngine`` joined it; since PR-016
(ADR-0019), ``SceneImageEngine``. Since PR-018 (ADR-0021),
``SubtitleEngine`` joins as a fourth -- the first with no Provider of
its own to coordinate, since it needs nothing beyond the ``Story``
already built.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from velora.workflows.story._types import NarratedStory

if TYPE_CHECKING:
    from velora.engines.narration_audio import NarrationAudioEngine
    from velora.engines.scene_image import SceneImageEngine
    from velora.engines.story import StoryEngine
    from velora.engines.subtitle import SubtitleEngine

__all__ = ["NarratedStory", "StoryWorkflow"]


class StoryWorkflow:
    """Runs the pipeline that turns a topic into a
    :class:`~velora.workflows.story.NarratedStory`.

    Wraps an injected :class:`~velora.engines.story.StoryEngine`,
    :class:`~velora.engines.narration_audio.NarrationAudioEngine`,
    :class:`~velora.engines.scene_image.SceneImageEngine`, and
    :class:`~velora.engines.subtitle.SubtitleEngine` -- never constructs
    any of them internally, and never imports ``velora.services`` or
    ``velora.providers`` directly (that would skip a layer of
    ADR-0012's canonical diagram, the same diagram ADR-0008 established
    for Engines/Services/Providers).
    """

    def __init__(
        self,
        story_engine: StoryEngine,
        narration_audio_engine: NarrationAudioEngine,
        scene_image_engine: SceneImageEngine,
        subtitle_engine: SubtitleEngine,
    ) -> None:
        self._story_engine = story_engine
        self._narration_audio_engine = narration_audio_engine
        self._scene_image_engine = scene_image_engine
        self._subtitle_engine = subtitle_engine

    def run(self, topic: str, *, max_tokens: int = 1024) -> NarratedStory:
        """Run the Workflow for ``topic``.

        Builds the :class:`~velora.engines.story.Story` first, then
        synthesizes, illustrates, and captions it, in that order. Only
        the first step is a genuine dependency of the rest -- synthesis,
        illustration, and captioning each depend only on the already-
        built ``Story``, not on each other, exactly as ADR-0019 already
        noted for synthesis versus illustration; captioning extends the
        same observation to a third, independent step.

        Returns a :class:`~velora.workflows.story.NarratedStory`,
        composing all four Engines' results -- the same "compose,
        don't flatten" resolution ADR-0016 established and ADR-0019
        already extended once, extended again here (ADR-0021).

        :raises ValueError: ``topic`` is empty or only whitespace.
        :raises ~velora.providers.VeloraProviderError: any underlying
            Provider failed -- see its own error hierarchy for
            specifics (authentication, rate limiting, connection, or
            other). Captioning has no Provider of its own and cannot
            fail this way. A failure synthesizing or illustrating
            leaves whatever was already built undelivered: no partial
            ``NarratedStory`` is returned, the same "no partial result"
            stance ``NarrationAudioEngine`` and ``SceneImageEngine``
            themselves already take per scene (ADR-0015, ADR-0019).
        """
        story = self._story_engine.build_story(topic, max_tokens=max_tokens)
        audio = self._narration_audio_engine.synthesize(story)
        images = self._scene_image_engine.illustrate(story)
        subtitles = self._subtitle_engine.caption(story)
        return NarratedStory(story=story, audio=audio, images=images, subtitles=subtitles)
