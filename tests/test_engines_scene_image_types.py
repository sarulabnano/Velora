"""Tests for velora.engines.scene_image type shapes."""

from __future__ import annotations

import dataclasses

import pytest

from velora.engines.scene_image import SceneImage, StoryImages


def test_scene_image_is_frozen() -> None:
    scene_image = SceneImage(index=0, image=b"abc", image_format="png")

    with pytest.raises(dataclasses.FrozenInstanceError):
        scene_image.image = b"changed"  # type: ignore[misc]


def test_story_images_holds_topic_and_scenes() -> None:
    scenes = (
        SceneImage(index=0, image=b"a", image_format="png"),
        SceneImage(index=1, image=b"b", image_format="png"),
    )

    story_images = StoryImages(topic="A city at dawn", scenes=scenes)

    assert story_images.topic == "A city at dawn"
    assert story_images.scenes == scenes


def test_story_images_permits_zero_scenes() -> None:
    story_images = StoryImages(topic="Empty", scenes=())

    assert story_images.scenes == ()


def test_story_images_is_frozen() -> None:
    story_images = StoryImages(topic="A city at dawn", scenes=())

    with pytest.raises(dataclasses.FrozenInstanceError):
        story_images.topic = "changed"  # type: ignore[misc]
