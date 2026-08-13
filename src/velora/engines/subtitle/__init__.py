"""The Subtitle Engine: captions a Story's scenes, timed by their audio.

Depends on ``velora.engines.story`` (for the ``Story`` type) and
``velora.engines.narration_audio`` (for the ``StoryAudio`` type it
times captions against, since PR-019/ADR-0022) — no
``velora.services`` or ``velora.providers`` dependency: no Provider
call is made here.
"""

from __future__ import annotations

from velora.engines.subtitle._duration import measure_duration_seconds
from velora.engines.subtitle._engine import SubtitleEngine
from velora.engines.subtitle._srt import render_srt
from velora.engines.subtitle._types import SceneSubtitle, StorySubtitles

__all__ = [
    "SceneSubtitle",
    "StorySubtitles",
    "SubtitleEngine",
    "measure_duration_seconds",
    "render_srt",
]
