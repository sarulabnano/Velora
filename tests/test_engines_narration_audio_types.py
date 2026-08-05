"""Tests for velora.engines.narration_audio type shapes."""

from __future__ import annotations

import dataclasses

import pytest

from velora.engines.narration_audio import SceneAudio, StoryAudio


def test_scene_audio_is_frozen() -> None:
    scene_audio = SceneAudio(index=0, audio=b"abc", audio_format="mp3")

    with pytest.raises(dataclasses.FrozenInstanceError):
        scene_audio.audio = b"changed"  # type: ignore[misc]


def test_story_audio_holds_topic_and_scenes() -> None:
    scenes = (
        SceneAudio(index=0, audio=b"a", audio_format="mp3"),
        SceneAudio(index=1, audio=b"b", audio_format="mp3"),
    )

    story_audio = StoryAudio(topic="A city at dawn", scenes=scenes)

    assert story_audio.topic == "A city at dawn"
    assert story_audio.scenes == scenes


def test_story_audio_permits_zero_scenes() -> None:
    story_audio = StoryAudio(topic="Empty", scenes=())

    assert story_audio.scenes == ()


def test_story_audio_is_frozen() -> None:
    story_audio = StoryAudio(topic="A city at dawn", scenes=())

    with pytest.raises(dataclasses.FrozenInstanceError):
        story_audio.topic = "changed"  # type: ignore[misc]
