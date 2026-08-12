"""Typed shapes produced by the Subtitle Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["SceneSubtitle", "StorySubtitles"]


@dataclass(frozen=True, slots=True)
class SceneSubtitle:
    """The caption cue for one :class:`~velora.engines.story.Scene`.

    Unlike :class:`~velora.engines.narration_audio.SceneAudio` and
    :class:`~velora.engines.scene_image.SceneImage`, this repeats the
    scene's ``text`` rather than correlating it back by ``index`` alone
    (ADR-0021): the caption's text *is* the artifact here — there is no
    separate binary payload a caller could read instead, the way audio
    bytes or image bytes stand in for their scene's text. Omitting it
    would make ``SceneSubtitle`` useless without also holding the
    original ``Story``.
    """

    index: int
    text: str
    start_seconds: float
    end_seconds: float


@dataclass(frozen=True, slots=True)
class StorySubtitles:
    """A :class:`~velora.engines.story.Story`, captioned scene by scene.

    ``scenes`` may be empty — mirrors every other per-scene result type
    in `velora.engines`: a story with no scenes has no captions, a
    valid state rather than an error.
    """

    topic: str
    scenes: Sequence[SceneSubtitle]
