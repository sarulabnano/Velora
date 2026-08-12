"""Typed shapes produced by the Story Workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from velora.engines.narration_audio import StoryAudio
    from velora.engines.scene_image import StoryImages
    from velora.engines.story import Story
    from velora.engines.subtitle import StorySubtitles

__all__ = ["NarratedStory"]


@dataclass(frozen=True, slots=True)
class NarratedStory:
    """A :class:`~velora.engines.story.Story`, paired with its
    :class:`~velora.engines.narration_audio.StoryAudio` (ADR-0016), its
    :class:`~velora.engines.scene_image.StoryImages` (ADR-0019), and,
    since PR-018 (ADR-0021), its
    :class:`~velora.engines.subtitle.StorySubtitles`.

    Composes the four Engines' own result types directly, rather than
    duplicating their fields into a new flat shape: each attribute is
    exactly what its corresponding Engine produces. A caller who only
    needs the text, the audio, the images, or the subtitles reads the
    corresponding attribute — nothing is re-derived or renamed on the
    way through the Workflow.
    """

    story: Story
    audio: StoryAudio
    images: StoryImages
    subtitles: StorySubtitles
