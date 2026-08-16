"""Tests for velora.engines.timeline.TimelineEngine."""

from __future__ import annotations

import pytest

from velora.engines.narration_audio import SceneAudio, StoryAudio
from velora.engines.scene_image import SceneImage, StoryImages
from velora.engines.story import Scene, Story
from velora.engines.subtitle import SceneSubtitle, StorySubtitles
from velora.engines.timeline import TimelineEngine


def _story(*scenes: tuple[int, str]) -> Story:
    return Story(topic="A day in the city", scenes=tuple(Scene(i, t) for i, t in scenes))


def _audio(*scenes: tuple[int, bytes]) -> StoryAudio:
    return StoryAudio(
        topic="A day in the city",
        scenes=tuple(SceneAudio(i, a, "mp3") for i, a in scenes),
    )


def _images(*scenes: tuple[int, bytes]) -> StoryImages:
    return StoryImages(
        topic="A day in the city",
        scenes=tuple(SceneImage(i, img, "png") for i, img in scenes),
    )


def _subtitles(*scenes: tuple[int, str, float, float]) -> StorySubtitles:
    return StorySubtitles(
        topic="A day in the city",
        scenes=tuple(SceneSubtitle(i, t, s, e) for i, t, s, e in scenes),
    )


def test_builds_one_timeline_scene_per_story_scene_in_order() -> None:
    engine = TimelineEngine()
    story = _story((0, "The city wakes."), (1, "The market opens."))
    audio = _audio((0, b"audio0"), (1, b"audio1"))
    images = _images((0, b"image0"), (1, b"image1"))
    subtitles = _subtitles((0, "The city wakes.", 0.0, 2.0), (1, "The market opens.", 2.0, 4.5))

    timeline = engine.build(story, audio, images, subtitles)

    assert [s.index for s in timeline.scenes] == [0, 1]
    assert timeline.topic == "A day in the city"


def test_each_timeline_scene_combines_all_four_sources() -> None:
    engine = TimelineEngine()
    story = _story((0, "The city wakes."))
    audio = _audio((0, b"audio-bytes"))
    images = _images((0, b"image-bytes"))
    subtitles = _subtitles((0, "The city wakes.", 0.0, 2.5))

    timeline = engine.build(story, audio, images, subtitles)

    scene = timeline.scenes[0]
    assert scene.text == "The city wakes."
    assert scene.audio == b"audio-bytes"
    assert scene.audio_format == "mp3"
    assert scene.image == b"image-bytes"
    assert scene.image_format == "png"
    assert scene.start_seconds == 0.0
    assert scene.end_seconds == 2.5


def test_reuses_subtitle_timing_rather_than_recomputing_it() -> None:
    engine = TimelineEngine()
    story = _story((0, "one two three four five"))  # would estimate differently if recomputed
    audio = _audio((0, b"audio-bytes"))
    images = _images((0, b"image-bytes"))
    subtitles = _subtitles((0, "one two three four five", 10.0, 20.0))  # deliberately unusual

    timeline = engine.build(story, audio, images, subtitles)

    assert timeline.scenes[0].start_seconds == 10.0
    assert timeline.scenes[0].end_seconds == 20.0


def test_empty_story_produces_an_empty_timeline() -> None:
    engine = TimelineEngine()
    story = _story()
    audio = _audio()
    images = _images()
    subtitles = _subtitles()

    timeline = engine.build(story, audio, images, subtitles)

    assert timeline.scenes == ()


def test_raises_when_a_scene_is_missing_from_audio() -> None:
    engine = TimelineEngine()
    story = _story((0, "Only scene."))
    audio = _audio()  # missing scene 0
    images = _images((0, b"image-bytes"))
    subtitles = _subtitles((0, "Only scene.", 0.0, 1.0))

    with pytest.raises(ValueError, match="missing"):
        engine.build(story, audio, images, subtitles)


def test_raises_when_a_scene_is_missing_from_images() -> None:
    engine = TimelineEngine()
    story = _story((0, "Only scene."))
    audio = _audio((0, b"audio-bytes"))
    images = _images()  # missing scene 0
    subtitles = _subtitles((0, "Only scene.", 0.0, 1.0))

    with pytest.raises(ValueError, match="missing"):
        engine.build(story, audio, images, subtitles)


def test_raises_when_a_scene_is_missing_from_subtitles() -> None:
    engine = TimelineEngine()
    story = _story((0, "Only scene."))
    audio = _audio((0, b"audio-bytes"))
    images = _images((0, b"image-bytes"))
    subtitles = _subtitles()  # missing scene 0

    with pytest.raises(ValueError, match="missing"):
        engine.build(story, audio, images, subtitles)
