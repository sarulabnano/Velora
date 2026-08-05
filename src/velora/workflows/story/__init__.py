"""The Story Workflow: the first real Workflow, orchestrating StoryEngine.

Depends on ``velora.engines.story`` — never on
``velora.services.narration`` or ``velora.providers`` directly
(ADR-0012's canonical layering: Workflows depends on Engines, not on
whatever an Engine itself depends on).
"""

from __future__ import annotations

from velora.workflows.story._workflow import StoryWorkflow

__all__ = ["StoryWorkflow"]
