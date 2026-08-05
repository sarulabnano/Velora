"""Tests for velora.engines.story type shapes."""

from __future__ import annotations

import dataclasses

import pytest

from velora.engines.story import Scene, Story


def test_scene_is_frozen() -> None:
    scene = Scene(index=0, text="Once upon a time.")

    with pytest.raises(dataclasses.FrozenInstanceError):
        scene.text = "changed"  # type: ignore[misc]


def test_story_holds_topic_and_scenes() -> None:
    scenes = (Scene(index=0, text="a"), Scene(index=1, text="b"))

    story = Story(topic="A city at dawn", scenes=scenes)

    assert story.topic == "A city at dawn"
    assert story.scenes == scenes


def test_story_permits_zero_scenes() -> None:
    story = Story(topic="Empty", scenes=())

    assert story.scenes == ()


def test_story_is_frozen() -> None:
    story = Story(topic="A city at dawn", scenes=())

    with pytest.raises(dataclasses.FrozenInstanceError):
        story.topic = "changed"  # type: ignore[misc]
