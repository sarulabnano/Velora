"""SubtitleEngine: captions a Story's scenes with estimated timing.

``docs/VISION.md`` lists "Subtitle Engine — Genera subtítulos" among
its Engine examples, without further detail on how timing should be
derived. This Engine estimates it from the scene text alone, via a
words-per-minute reading-pace heuristic (ADR-0021) — no Provider, no
external call, and consequently no dependency on any Service: the
first Engine in `velora.engines` that is pure computation over a
`Story` it already has.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from velora.engines.subtitle._types import SceneSubtitle, StorySubtitles

if TYPE_CHECKING:
    from velora.engines.story import Story

__all__ = ["SubtitleEngine"]

_DEFAULT_WORDS_PER_MINUTE = 150.0


class SubtitleEngine:
    """Captions a :class:`~velora.engines.story.Story` into
    :class:`~velora.engines.subtitle.StorySubtitles`.

    No Service or Provider is injected — unlike every other Engine in
    `velora.engines`, there is nothing external to call: timing is
    estimated purely from each scene's word count and
    ``words_per_minute``, a deliberately simple stand-in for the actual
    audio duration `NarrationAudioEngine` produces (ADR-0021 explains
    why measuring the real audio is out of scope for now).
    """

    def __init__(self, *, words_per_minute: float = _DEFAULT_WORDS_PER_MINUTE) -> None:
        if words_per_minute <= 0:
            raise ValueError("words_per_minute must be positive.")
        self._words_per_minute = words_per_minute

    def caption(self, story: Story) -> StorySubtitles:
        """Caption every scene in ``story``, in order.

        Each scene's estimated duration is
        ``word_count / words_per_minute * 60`` seconds; scenes are
        captioned back-to-back, with no gap — the first scene starts at
        ``0.0``, and each following scene starts exactly where the
        previous one ends.
        """
        scenes = []
        cursor = 0.0
        for scene in story.scenes:
            word_count = len(scene.text.split())
            duration_seconds = (word_count / self._words_per_minute) * 60.0
            end = cursor + duration_seconds
            scenes.append(
                SceneSubtitle(
                    index=scene.index,
                    text=scene.text,
                    start_seconds=cursor,
                    end_seconds=end,
                )
            )
            cursor = end
        return StorySubtitles(topic=story.topic, scenes=tuple(scenes))
