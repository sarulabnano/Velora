"""StoryEngine: builds a Story from a topic.

``docs/VISION.md``: "Los Engines ejecutan lógica compleja... Story
Engine construye la historia." This is the first Engine: it generates
narration text via an injected
:class:`~velora.services.narration.NarrationService` and divides it into
ordered :class:`~velora.engines.story.Scene` instances.

Scope, deliberate:

- Scene division is a pure, deterministic split on paragraph breaks in
  the returned text — not a prompt-format contract with the underlying
  model. A Provider that ignores formatting instructions (a real
  possibility, not a hypothetical) would silently produce a wrong
  result if scene boundaries depended on the model following a
  delimiter convention; splitting on paragraphs does not depend on
  that.
- No target scene count. Merging or splitting paragraphs to hit an
  exact number is a real, separate design problem with no concrete
  specification yet — better left unbuilt than built wrong.
- No automated research step: `docs/VISION.md`'s "investigar" stage
  needs a research Provider that does not exist yet.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from velora.engines.story._types import Scene, Story

if TYPE_CHECKING:
    from velora.services.narration import NarrationService

__all__ = ["StoryEngine"]

_PARAGRAPH_BREAK = re.compile(r"\n\s*\n")

_DEFAULT_INSTRUCTIONS_TEMPLATE = (
    "Write a narration about: {topic}. Structure it as a sequence of "
    "distinct scenes, each a short paragraph. Separate scenes with a "
    "blank line."
)


def _split_into_scenes(text: str) -> tuple[Scene, ...]:
    paragraphs = (part.strip() for part in _PARAGRAPH_BREAK.split(text.strip()))
    non_empty = [p for p in paragraphs if p]
    return tuple(Scene(index=i, text=p) for i, p in enumerate(non_empty))


class StoryEngine:
    """Builds a :class:`Story` from a topic, via an injected
    :class:`~velora.services.narration.NarrationService`.

    Contains the "how to turn narration text into scenes" logic —
    exactly the kind of orchestration/decision-making that separates an
    Engine from the Service it depends on (ADR-0008: `NarrationService`
    itself is deliberately thin and makes no such decisions).
    """

    def __init__(self, narration_service: NarrationService) -> None:
        self._narration_service = narration_service

    def build_story(self, topic: str, *, max_tokens: int = 1024) -> Story:
        """Generate a :class:`Story` about ``topic``.

        :raises ValueError: ``topic`` is empty or only whitespace.
        :raises ~velora.providers.VeloraProviderError: the underlying
            Provider failed.
        """
        if not topic.strip():
            raise ValueError("topic must not be empty.")

        instructions = _DEFAULT_INSTRUCTIONS_TEMPLATE.format(topic=topic)
        result = self._narration_service.narrate(instructions, max_tokens=max_tokens)
        scenes = _split_into_scenes(result.text)
        return Story(topic=topic, scenes=scenes)
