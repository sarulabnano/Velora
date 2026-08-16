"""Typed shapes produced by the Timeline Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["Timeline", "TimelineScene"]


@dataclass(frozen=True, slots=True)
class TimelineScene:
    """One scene, with everything a Render step would need for it
    aligned in a single place: its text, its audio, its image, and the
    time window it occupies.

    Unlike ``SceneAudio``/``SceneImage``/``SceneSubtitle`` — each one
    Engine's own output, correlated back to a ``Story`` by ``index``
    alone — this repeats every field, because it exists specifically to
    remove the need to correlate four separate collections by hand
    (ADR-0023). ``start_seconds``/``end_seconds`` are the same values
    :class:`~velora.engines.subtitle.SceneSubtitle` already computed
    from the scene's real audio duration — not re-measured here.
    """

    index: int
    text: str
    audio: bytes
    audio_format: str
    image: bytes
    image_format: str
    start_seconds: float
    end_seconds: float


@dataclass(frozen=True, slots=True)
class Timeline:
    """A :class:`~velora.engines.story.Story`, organized into one
    ordered, time-aligned sequence of :class:`TimelineScene`.

    ``scenes`` may be empty — mirrors every other per-scene result type
    in `velora.engines`: a story with no scenes has no timeline, a
    valid state rather than an error.
    """

    topic: str
    scenes: Sequence[TimelineScene]
