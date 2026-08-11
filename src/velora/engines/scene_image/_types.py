"""Typed shapes produced by the Scene Image Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["SceneImage", "StoryImages"]


@dataclass(frozen=True, slots=True)
class SceneImage:
    """The generated image for one :class:`~velora.engines.story.Scene`.

    Does not repeat the scene's text: ``index`` is enough to correlate
    this back to the original :class:`~velora.engines.story.Story` a
    caller already holds — same reasoning
    :class:`~velora.engines.narration_audio.SceneAudio` already applied
    (ADR-0015).
    """

    index: int
    image: bytes
    image_format: str


@dataclass(frozen=True, slots=True)
class StoryImages:
    """A :class:`~velora.engines.story.Story`, illustrated with one
    image per scene.

    Named ``StoryImages`` (plural), not ``StoryImage`` — unlike audio,
    a mass noun that reads naturally in the singular even when it
    covers several scenes (``StoryAudio``), a *story's images* are a
    countable set, one per scene; the plural is the accurate name for
    what this type actually holds (ADR-0019). ``scenes`` may be empty —
    mirrors :class:`~velora.engines.story.Story` and
    :class:`~velora.engines.narration_audio.StoryAudio`: a story with
    no scenes produces no images, a valid state rather than an error.
    """

    topic: str
    scenes: Sequence[SceneImage]
