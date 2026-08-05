"""The Narration Audio Engine: synthesizes a Story's scenes into audio.

Depends on ``velora.services.voice`` — never on ``velora.providers``
directly (ADR-0008's canonical layering: Engines depends on capability
Services, not on Providers). Also depends on ``velora.engines.story``,
for the ``Story`` type it receives as input.
"""

from __future__ import annotations

from velora.engines.narration_audio._engine import NarrationAudioEngine
from velora.engines.narration_audio._types import SceneAudio, StoryAudio

__all__ = ["NarrationAudioEngine", "SceneAudio", "StoryAudio"]
