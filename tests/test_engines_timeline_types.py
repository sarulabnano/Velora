"""Tests for velora.engines.timeline type shapes."""

from __future__ import annotations

import dataclasses

import pytest

from velora.engines.timeline import Timeline, TimelineScene


def test_timeline_scene_is_frozen() -> None:
    scene = TimelineScene(
        index=0,
        text="Hi",
        audio=b"a",
        audio_format="mp3",
        image=b"i",
        image_format="png",
        start_seconds=0.0,
        end_seconds=1.0,
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        scene.text = "changed"  # type: ignore[misc]


def test_timeline_scene_holds_all_its_fields() -> None:
    scene = TimelineScene(
        index=3,
        text="The city wakes.",
        audio=b"audio-bytes",
        audio_format="mp3",
        image=b"image-bytes",
        image_format="png",
        start_seconds=4.0,
        end_seconds=6.5,
    )

    assert scene.index == 3
    assert scene.text == "The city wakes."
    assert scene.audio == b"audio-bytes"
    assert scene.audio_format == "mp3"
    assert scene.image == b"image-bytes"
    assert scene.image_format == "png"
    assert scene.start_seconds == 4.0
    assert scene.end_seconds == 6.5


def test_timeline_permits_zero_scenes() -> None:
    timeline = Timeline(topic="Empty", scenes=())

    assert timeline.scenes == ()


def test_timeline_is_frozen() -> None:
    timeline = Timeline(topic="A city at dawn", scenes=())

    with pytest.raises(dataclasses.FrozenInstanceError):
        timeline.topic = "changed"  # type: ignore[misc]
