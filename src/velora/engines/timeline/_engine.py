"""TimelineEngine: organizes a Story's scenes into one aligned timeline.

``docs/VISION.md`` lists "Timeline Engine — Organiza escenas" among its
Engine examples, and places "construir timeline" right after "generar
imagenes" and before "renderizar" in its example pipeline: the step
that takes everything the earlier steps generated and arranges it into
the single structure a future Render step would consume, rather than
four separate parallel results a renderer would otherwise have to
correlate by hand.

No Service or Provider is injected — like
:class:`~velora.engines.subtitle.SubtitleEngine`, there is nothing
external to call: this Engine only reorganizes results the other three
Engines already produced.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from velora.engines.timeline._types import Timeline, TimelineScene

if TYPE_CHECKING:
    from velora.engines.narration_audio import StoryAudio
    from velora.engines.scene_image import StoryImages
    from velora.engines.story import Story
    from velora.engines.subtitle import StorySubtitles

__all__ = ["TimelineEngine"]


class TimelineEngine:
    """Organizes a :class:`~velora.engines.story.Story` and its
    generated audio, images, and subtitles into a single
    :class:`~velora.engines.timeline.Timeline`.
    """

    def build(
        self,
        story: Story,
        audio: StoryAudio,
        images: StoryImages,
        subtitles: StorySubtitles,
    ) -> Timeline:
        """Build the timeline for ``story``.

        Every argument is expected to describe the exact same
        ``story.scenes`` — the shape every
        :class:`~velora.workflows.story.StoryWorkflow` run already
        guarantees, since all four are built from the same ``Story``.
        This isn't the same situation
        :class:`~velora.engines.subtitle.SubtitleEngine` handles when a
        single clip of audio can't be parsed (an ordinary, expected
        failure mode of an external Provider, ADR-0022): a scene
        genuinely missing from ``audio``, ``images``, or ``subtitles``
        here means the four arguments don't actually describe the same
        ``Story``, a caller error rather than something to degrade
        gracefully from.

        :raises ValueError: a scene in ``story.scenes`` has no matching
            entry (by ``index``) in ``audio``, ``images``, or
            ``subtitles``.
        """
        audio_by_index = {scene_audio.index: scene_audio for scene_audio in audio.scenes}
        images_by_index = {scene_image.index: scene_image for scene_image in images.scenes}
        subtitles_by_index = {
            scene_subtitle.index: scene_subtitle for scene_subtitle in subtitles.scenes
        }

        scenes = []
        for scene in story.scenes:
            scene_audio = audio_by_index.get(scene.index)
            scene_image = images_by_index.get(scene.index)
            scene_subtitle = subtitles_by_index.get(scene.index)
            if scene_audio is None or scene_image is None or scene_subtitle is None:
                raise ValueError(
                    f"Scene {scene.index} is missing from the given audio, images, "
                    "or subtitles — they must all describe the same Story."
                )
            scenes.append(
                TimelineScene(
                    index=scene.index,
                    text=scene.text,
                    audio=scene_audio.audio,
                    audio_format=scene_audio.audio_format,
                    image=scene_image.image,
                    image_format=scene_image.image_format,
                    start_seconds=scene_subtitle.start_seconds,
                    end_seconds=scene_subtitle.end_seconds,
                )
            )
        return Timeline(topic=story.topic, scenes=tuple(scenes))
