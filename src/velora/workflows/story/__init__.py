"""The Story Workflow: orchestrates StoryEngine and NarrationAudioEngine.

Depends on ``velora.engines.story`` and
``velora.engines.narration_audio`` — never on ``velora.services`` or
``velora.providers`` directly (ADR-0012's canonical layering: Workflows
depends on Engines, not on whatever an Engine itself depends on). Since
PR-013 (ADR-0016), coordinates both real Engines rather than just the
first.
"""

from __future__ import annotations

from velora.workflows.story._types import NarratedStory
from velora.workflows.story._workflow import StoryWorkflow

__all__ = ["NarratedStory", "StoryWorkflow"]
