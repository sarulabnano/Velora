"""The Timeline Engine: organizes a Story's generated scenes into one
time-aligned sequence.

Depends on ``velora.engines.story``, ``velora.engines.narration_audio``,
``velora.engines.scene_image``, and ``velora.engines.subtitle`` — for
the four types it combines. No ``velora.services`` or
``velora.providers`` dependency: no Provider call is made here.
"""

from __future__ import annotations

from velora.engines.timeline._engine import TimelineEngine
from velora.engines.timeline._types import Timeline, TimelineScene

__all__ = ["Timeline", "TimelineEngine", "TimelineScene"]
