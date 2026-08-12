"""The Subtitle Engine: captions a Story's scenes with estimated timing.

Depends on ``velora.engines.story`` only, for the ``Story`` type it
receives as input — no ``velora.services`` or ``velora.providers``
dependency at all (ADR-0021): this is the first Engine in
``velora.engines`` with no external call to make.
"""

from __future__ import annotations

from velora.engines.subtitle._engine import SubtitleEngine
from velora.engines.subtitle._srt import render_srt
from velora.engines.subtitle._types import SceneSubtitle, StorySubtitles

__all__ = ["SceneSubtitle", "StorySubtitles", "SubtitleEngine", "render_srt"]
