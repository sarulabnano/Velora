"""Rendering StorySubtitles as SubRip (.srt) text.

Kept separate from `_engine.py`: `SubtitleEngine.caption()` produces a
provider-agnostic, format-agnostic `StorySubtitles` (ADR-0021) — the
same "typed result first, serialization is a separate concern" split
`velora.engines.story` already draws between `Story` and whatever
prints it. SRT is one possible rendering, not the only one a future
caller might want (WebVTT is a plausible second); keeping it in its own
function makes that boundary explicit rather than baking one format
into the Engine's own output type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from velora.engines.subtitle._types import StorySubtitles

__all__ = ["render_srt"]


def _format_timestamp(seconds: float) -> str:
    total_milliseconds = round(seconds * 1000)
    hours, remainder = divmod(total_milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def render_srt(subtitles: StorySubtitles) -> str:
    """Render ``subtitles`` as SubRip (.srt) text.

    SRT cue numbers are 1-based, per the format's own convention —
    independent of each scene's own ``index`` (which starts at 0, like
    every other per-scene type in `velora.engines`).
    """
    blocks = []
    for cue_number, scene in enumerate(subtitles.scenes, start=1):
        start = _format_timestamp(scene.start_seconds)
        end = _format_timestamp(scene.end_seconds)
        blocks.append(f"{cue_number}\n{start} --> {end}\n{scene.text}\n")
    return "\n".join(blocks)
