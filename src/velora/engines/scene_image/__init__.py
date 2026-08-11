"""The Scene Image Engine: illustrates a Story's scenes with images.

Depends on ``velora.services.image`` -- never on ``velora.providers``
directly (ADR-0008's canonical layering: Engines depends on capability
Services, not on Providers). Also depends on ``velora.engines.story``,
for the ``Story`` type it receives as input.
"""

from __future__ import annotations

from velora.engines.scene_image._engine import SceneImageEngine
from velora.engines.scene_image._types import SceneImage, StoryImages

__all__ = ["SceneImage", "SceneImageEngine", "StoryImages"]
