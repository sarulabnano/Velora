"""StoryWorkflow: orchestrates the Engines needed to turn a topic into a
narrated, synthesized Story.

``docs/VISION.md``: "Los Workflows conectan todos los motores." Through
PR-012 that was exactly one motor -- ``StoryEngine`` -- the smallest
possible real Workflow (ADR-0012). Since PR-013 (ADR-0016), with a
second Engine now real (``NarrationAudioEngine``), ``StoryWorkflow``
coordinates both: it builds a :class:`~velora.engines.story.Story` via
``StoryEngine``, then synthesizes it into
:class:`~velora.engines.narration_audio.StoryAudio` via
``NarrationAudioEngine``, in that order -- exactly the question
ADR-0012 deliberately left open ("revelaria si la forma actual de
`StoryWorkflow` sigue siendo la correcta o necesita crecer").
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from velora.workflows.story._types import NarratedStory

if TYPE_CHECKING:
    from velora.engines.narration_audio import NarrationAudioEngine
    from velora.engines.story import StoryEngine

__all__ = ["NarratedStory", "StoryWorkflow"]


class StoryWorkflow:
    """Runs the pipeline that turns a topic into a
    :class:`~velora.workflows.story.NarratedStory`.

    Wraps an injected :class:`~velora.engines.story.StoryEngine` and
    :class:`~velora.engines.narration_audio.NarrationAudioEngine` --
    never constructs either internally, and never imports
    ``velora.services`` or ``velora.providers`` directly (that would
    skip a layer of ADR-0012's canonical diagram, the same diagram
    ADR-0008 established for Engines/Services/Providers).
    """

    def __init__(
        self,
        story_engine: StoryEngine,
        narration_audio_engine: NarrationAudioEngine,
    ) -> None:
        self._story_engine = story_engine
        self._narration_audio_engine = narration_audio_engine

    def run(self, topic: str, *, max_tokens: int = 1024) -> NarratedStory:
        """Run the Workflow for ``topic``.

        Builds the :class:`~velora.engines.story.Story` first, then
        synthesizes it -- the same order ``docs/VISION.md``'s example
        pipeline lists ("dividir escenas" before "generar voz"), and the
        only order that makes sense: audio synthesis needs the scenes
        the first step produces.

        Returns a :class:`~velora.workflows.story.NarratedStory`,
        pairing both Engines' results, rather than the bare ``Story``
        this method returned through PR-012 -- the same "new type that
        composes both" resolution ``PROJECT_CONTEXT.md`` posed as the
        open question for this PR (ADR-0016).

        :raises ValueError: ``topic`` is empty or only whitespace.
        :raises ~velora.providers.VeloraProviderError: either
            underlying Provider failed -- see its own error hierarchy
            for specifics (authentication, rate limiting, connection,
            or other). A failure synthesizing audio leaves the
            already-built ``Story`` undelivered: no partial
            ``NarratedStory`` is returned, the same "no partial result"
            stance ``NarrationAudioEngine`` itself already takes per
            scene (ADR-0015).
        """
        story = self._story_engine.build_story(topic, max_tokens=max_tokens)
        audio = self._narration_audio_engine.synthesize(story)
        return NarratedStory(story=story, audio=audio)
