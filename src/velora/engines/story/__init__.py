"""The Story Engine: builds a Story from a topic.

Depends on ``velora.services.narration`` — never on
``velora.providers`` directly (ADR-0008's canonical layering: Engines
depends on capability Services, not on Providers).
"""

from __future__ import annotations

from velora.engines.story._engine import StoryEngine
from velora.engines.story._types import Scene, Story

__all__ = ["Scene", "Story", "StoryEngine"]
