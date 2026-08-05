"""Typed shapes produced by the Narration Audio Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["SceneAudio", "StoryAudio"]


@dataclass(frozen=True, slots=True)
class SceneAudio:
    """The synthesized audio for one :class:`~velora.engines.story.Scene`.

    Does not repeat the scene's text: ``index`` is enough to correlate
    this back to the original :class:`~velora.engines.story.Story` a
    caller already holds (ADR-0015).
    """

    index: int
    audio: bytes
    audio_format: str


@dataclass(frozen=True, slots=True)
class StoryAudio:
    """A :class:`~velora.engines.story.Story`, synthesized into audio,
    scene by scene.

    ``scenes`` may be empty — mirrors
    :class:`~velora.engines.story.Story` itself: a story with no scenes
    produces no audio, a valid state rather than an error.
    """

    topic: str
    scenes: Sequence[SceneAudio]
