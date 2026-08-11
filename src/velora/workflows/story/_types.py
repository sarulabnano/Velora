"""Typed shapes produced by the Story Workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from velora.engines.narration_audio import StoryAudio
    from velora.engines.scene_image import StoryImages
    from velora.engines.story import Story

__all__ = ["NarratedStory"]


@dataclass(frozen=True, slots=True)
class NarratedStory:
    """A :class:`~velora.engines.story.Story`, paired with its
    :class:`~velora.engines.narration_audio.StoryAudio` (ADR-0016) and,
    since PR-016 (ADR-0019), its
    :class:`~velora.engines.scene_image.StoryImages`.

    Composes the three Engines' own result types directly, rather than
    duplicating their fields into a new flat shape: ``story`` is exactly
    what :class:`~velora.engines.story.StoryEngine` produces, ``audio``
    is exactly what :class:`~velora.engines.narration_audio.
    NarrationAudioEngine` produces from it, ``images`` is exactly what
    :class:`~velora.engines.scene_image.SceneImageEngine` produces from
    it. A caller who only needs the text, only the audio, or only the
    images reads the corresponding attribute -- nothing is re-derived or
    renamed on the way through the Workflow.
    """

    story: Story
    audio: StoryAudio
    images: StoryImages
