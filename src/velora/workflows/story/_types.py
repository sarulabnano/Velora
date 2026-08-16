"""Typed shapes produced by the Story Workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from velora.engines.narration_audio import StoryAudio
    from velora.engines.scene_image import StoryImages
    from velora.engines.story import Story
    from velora.engines.subtitle import StorySubtitles
    from velora.engines.timeline import Timeline

__all__ = ["NarratedStory"]


@dataclass(frozen=True, slots=True)
class NarratedStory:
    """A :class:`~velora.engines.story.Story`, paired with its
    :class:`~velora.engines.narration_audio.StoryAudio` (ADR-0016), its
    :class:`~velora.engines.scene_image.StoryImages` (ADR-0019), its
    :class:`~velora.engines.subtitle.StorySubtitles` (ADR-0021), and,
    since PR-020 (ADR-0023), its
    :class:`~velora.engines.timeline.Timeline`.

    Composes the five Engines' own result types directly, rather than
    duplicating their fields into a new flat shape: each attribute is
    exactly what its corresponding Engine produces. ``timeline`` is not
    redundant with the other four: those are each one Engine's own
    output, kept separately attributable; ``timeline`` is
    ``TimelineEngine``'s own synthesis of all four into the single,
    per-scene-aligned sequence a future Render step needs, not a
    restatement of what the other fields already say.
    """

    story: Story
    audio: StoryAudio
    images: StoryImages
    subtitles: StorySubtitles
    timeline: Timeline
