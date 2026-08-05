"""StoryWorkflow: orchestrates the Engines needed to turn a topic into a Story.

``docs/VISION.md``: "Los Workflows conectan todos los motores." Today
that is exactly one motor — ``StoryEngine`` — the smallest possible real
Workflow. ADR-0012 explains why this thin, single-Engine shape is built
now rather than waiting for a second Engine to actually coordinate: the
same precedent ADR-0010 already set for ``NarrationService`` before any
Engine existed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from velora.engines.story import Story, StoryEngine

__all__ = ["StoryWorkflow"]


class StoryWorkflow:
    """Runs the pipeline that turns a topic into a
    :class:`~velora.engines.story.Story`.

    Wraps an injected :class:`~velora.engines.story.StoryEngine` — never
    constructs one internally, and never imports
    ``velora.services.narration`` or ``velora.providers`` directly (that
    would skip a layer of ADR-0012's canonical diagram, the same
    diagram ADR-0008 established for Engines/Services/Providers).
    """

    def __init__(self, story_engine: StoryEngine) -> None:
        self._story_engine = story_engine

    def run(self, topic: str, *, max_tokens: int = 1024) -> Story:
        """Run the Workflow for ``topic``.

        Reuses :class:`~velora.engines.story.Story` as its result type
        directly, rather than wrapping it in a new type — the same
        reasoning ADR-0010 already applied to ``NarrationService``
        reusing ``TextGenerationResult``: a ``Story`` is already
        Workflow-agnostic, so wrapping it again would add ceremony, not
        independence.

        :raises ValueError: ``topic`` is empty or only whitespace.
        :raises ~velora.providers.VeloraProviderError: the underlying
            Provider failed — see its own error hierarchy for specifics
            (authentication, rate limiting, connection, or other).
        """
        return self._story_engine.build_story(topic, max_tokens=max_tokens)
