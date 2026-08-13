"""SubtitleEngine: captions a Story's scenes, timed by their real audio.

``docs/VISION.md`` lists "Subtitle Engine — Genera subtítulos" among
its Engine examples, without further detail on how timing should be
derived. Since PR-019 (ADR-0022), each scene's duration is measured
from the actual audio `NarrationAudioEngine` already produced for it
(via `velora.engines.subtitle.measure_duration_seconds`) — not
estimated from word count, the approach PR-018 (ADR-0021) shipped
first, kept now only as a fallback for when a duration can't be
measured (see `caption` below).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from velora.engines.subtitle._duration import measure_duration_seconds
from velora.engines.subtitle._types import SceneSubtitle, StorySubtitles

if TYPE_CHECKING:
    from velora.engines.narration_audio import StoryAudio
    from velora.engines.story import Story

__all__ = ["SubtitleEngine"]

_DEFAULT_WORDS_PER_MINUTE = 150.0


class SubtitleEngine:
    """Captions a :class:`~velora.engines.story.Story` into
    :class:`~velora.engines.subtitle.StorySubtitles`, timed by its
    :class:`~velora.engines.narration_audio.StoryAudio`.

    No Service or Provider is injected (ADR-0021) — `caption()` reads
    the audio bytes a caller already has, rather than calling anything
    itself. `words_per_minute` is a fallback, not the primary source of
    timing since PR-019 (ADR-0022): used only for a scene whose audio
    duration `measure_duration_seconds` couldn't determine.
    """

    def __init__(self, *, words_per_minute: float = _DEFAULT_WORDS_PER_MINUTE) -> None:
        if words_per_minute <= 0:
            raise ValueError("words_per_minute must be positive.")
        self._words_per_minute = words_per_minute

    def caption(self, story: Story, audio: StoryAudio) -> StorySubtitles:
        """Caption every scene in ``story``, in order, timed by ``audio``.

        For each scene, looks up the matching
        :class:`~velora.engines.narration_audio.SceneAudio` by index and
        measures its real duration. If no matching scene audio exists,
        or its duration couldn't be measured (an unsupported or corrupt
        format — see `measure_duration_seconds`), falls back to the
        ``word_count / words_per_minute * 60`` estimate PR-018
        (ADR-0021) originally shipped, so a single unreadable clip
        degrades that one scene's timing rather than aborting
        captioning entirely.

        Scenes are captioned back-to-back, with no gap — the first
        scene starts at ``0.0``, and each following scene starts
        exactly where the previous one ends.
        """
        audio_by_index = {scene_audio.index: scene_audio for scene_audio in audio.scenes}

        scenes = []
        cursor = 0.0
        for scene in story.scenes:
            scene_audio = audio_by_index.get(scene.index)
            duration_seconds = (
                measure_duration_seconds(scene_audio.audio) if scene_audio is not None else None
            )
            if duration_seconds is None:
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
