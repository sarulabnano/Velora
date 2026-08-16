"""StoryWorkflow: orchestrates the Engines needed to turn a topic into a
narrated, synthesized, illustrated, captioned, timelined Story.

``docs/VISION.md``: "Los Workflows conectan todos los motores." Through
PR-012 that was exactly one motor -- ``StoryEngine``. Since PR-013
(ADR-0016), ``NarrationAudioEngine`` joined it; since PR-016
(ADR-0019), ``SceneImageEngine``; since PR-018 (ADR-0021),
``SubtitleEngine``. Since PR-020 (ADR-0023), ``TimelineEngine`` joins
as a fifth -- the first that depends on the outputs of all three
preceding Engines at once, rather than only on the ``Story`` (and, for
``SubtitleEngine`` since ADR-0022, its audio).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from velora.workflows.story._types import NarratedStory

if TYPE_CHECKING:
    from velora.engines.narration_audio import NarrationAudioEngine
    from velora.engines.scene_image import SceneImageEngine
    from velora.engines.story import StoryEngine
    from velora.engines.subtitle import SubtitleEngine
    from velora.engines.timeline import TimelineEngine

__all__ = ["NarratedStory", "StoryWorkflow"]


class StoryWorkflow:
    """Runs the pipeline that turns a topic into a
    :class:`~velora.workflows.story.NarratedStory`.

    Wraps an injected :class:`~velora.engines.story.StoryEngine`,
    :class:`~velora.engines.narration_audio.NarrationAudioEngine`,
    :class:`~velora.engines.scene_image.SceneImageEngine`,
    :class:`~velora.engines.subtitle.SubtitleEngine`, and
    :class:`~velora.engines.timeline.TimelineEngine` -- never constructs
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
        timeline_engine: TimelineEngine,
    ) -> None:
        self._story_engine = story_engine
        self._narration_audio_engine = narration_audio_engine
        self._scene_image_engine = scene_image_engine
        self._subtitle_engine = subtitle_engine
        self._timeline_engine = timeline_engine

    def run(self, topic: str, *, max_tokens: int = 1024) -> NarratedStory:
        """Run the Workflow for ``topic``.

        Builds the :class:`~velora.engines.story.Story` first, then
        synthesizes, illustrates, and captions it -- illustration
        depends only on the ``Story``, captioning also needs the
        already-synthesized audio (ADR-0022), so both must run after
        synthesis, in either order relative to each other. Building the
        timeline runs last, since it's the first step that needs all
        three of the prior Engines' outputs at once -- it cannot start
        until synthesis, illustration, and captioning have all
        completed.

        Returns a :class:`~velora.workflows.story.NarratedStory`,
        composing all five Engines' results -- the same "compose,
        don't flatten" resolution ADR-0016 established, extended by
        ADR-0019 and ADR-0021, extended again here (ADR-0023).

        :raises ValueError: ``topic`` is empty or only whitespace.
            ``TimelineEngine.build`` can also raise ``ValueError`` if
            its inputs describe mismatched scenes, but every input it
            receives here comes from the same ``story``, so that
            precondition can never actually fail through this method.
        :raises ~velora.providers.VeloraProviderError: any underlying
            Provider failed -- see its own error hierarchy for
            specifics (authentication, rate limiting, connection, or
            other). Captioning and timeline-building have no Provider
            of their own and cannot fail this way. A failure
            synthesizing or illustrating leaves whatever was already
            built undelivered: no partial ``NarratedStory`` is
            returned, the same "no partial result" stance
            ``NarrationAudioEngine`` and ``SceneImageEngine``
            themselves already take per scene (ADR-0015, ADR-0019).
        """
        story = self._story_engine.build_story(topic, max_tokens=max_tokens)
        audio = self._narration_audio_engine.synthesize(story)
        images = self._scene_image_engine.illustrate(story)
        subtitles = self._subtitle_engine.caption(story, audio)
        timeline = self._timeline_engine.build(story, audio, images, subtitles)
        return NarratedStory(
            story=story, audio=audio, images=images, subtitles=subtitles, timeline=timeline
        )
