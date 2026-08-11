"""StoryWorkflow: orchestrates the Engines needed to turn a topic into a
narrated, synthesized, illustrated Story.

``docs/VISION.md``: "Los Workflows conectan todos los motores." Through
PR-012 that was exactly one motor -- ``StoryEngine`` -- the smallest
possible real Workflow (ADR-0012). Since PR-013 (ADR-0016), with a
second Engine real (``NarrationAudioEngine``), ``StoryWorkflow``
coordinated both. Since PR-016 (ADR-0019), with a third Engine real
(``SceneImageEngine``), it coordinates all three: it builds a
:class:`~velora.engines.story.Story` via ``StoryEngine``, synthesizes it
into :class:`~velora.engines.narration_audio.StoryAudio` via
``NarrationAudioEngine``, and illustrates it into
:class:`~velora.engines.scene_image.StoryImages` via
``SceneImageEngine`` -- in that order.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from velora.workflows.story._types import NarratedStory

if TYPE_CHECKING:
    from velora.engines.narration_audio import NarrationAudioEngine
    from velora.engines.scene_image import SceneImageEngine
    from velora.engines.story import StoryEngine

__all__ = ["NarratedStory", "StoryWorkflow"]


class StoryWorkflow:
    """Runs the pipeline that turns a topic into a
    :class:`~velora.workflows.story.NarratedStory`.

    Wraps an injected :class:`~velora.engines.story.StoryEngine`,
    :class:`~velora.engines.narration_audio.NarrationAudioEngine`, and
    :class:`~velora.engines.scene_image.SceneImageEngine` -- never
    constructs any of them internally, and never imports
    ``velora.services`` or ``velora.providers`` directly (that would
    skip a layer of ADR-0012's canonical diagram, the same diagram
    ADR-0008 established for Engines/Services/Providers).
    """

    def __init__(
        self,
        story_engine: StoryEngine,
        narration_audio_engine: NarrationAudioEngine,
        scene_image_engine: SceneImageEngine,
    ) -> None:
        self._story_engine = story_engine
        self._narration_audio_engine = narration_audio_engine
        self._scene_image_engine = scene_image_engine

    def run(self, topic: str, *, max_tokens: int = 1024) -> NarratedStory:
        """Run the Workflow for ``topic``.

        Builds the :class:`~velora.engines.story.Story` first, then
        synthesizes it, then illustrates it -- the same order
        ``docs/VISION.md``'s example pipeline lists ("dividir escenas"
        before "generar voz" before "generar imagenes"), and the only
        order that makes sense: both synthesis and illustration need the
        scenes the first step produces. Synthesis runs before
        illustration only because that is the order PR-013 (ADR-0016)
        already established for the first two Engines; illustration does
        not depend on the audio in any way -- a future PR could
        parallelize or reorder these two without changing either
        Engine's contract.

        Returns a :class:`~velora.workflows.story.NarratedStory`,
        composing all three Engines' results, rather than the
        two-Engine version this method returned through PR-013 --
        the same "compose, don't flatten" resolution ADR-0016 already
        established, extended to a third Engine (ADR-0019).

        :raises ValueError: ``topic`` is empty or only whitespace.
        :raises ~velora.providers.VeloraProviderError: any underlying
            Provider failed -- see its own error hierarchy for
            specifics (authentication, rate limiting, connection, or
            other). A failure synthesizing or illustrating leaves
            whatever was already built undelivered: no partial
            ``NarratedStory`` is returned, the same "no partial result"
            stance ``NarrationAudioEngine`` and ``SceneImageEngine``
            themselves already take per scene (ADR-0015, ADR-0019).
        """
        story = self._story_engine.build_story(topic, max_tokens=max_tokens)
        audio = self._narration_audio_engine.synthesize(story)
        images = self._scene_image_engine.illustrate(story)
        return NarratedStory(story=story, audio=audio, images=images)
