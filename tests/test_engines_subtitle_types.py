"""Tests for velora.engines.subtitle type shapes."""

from __future__ import annotations

import dataclasses

import pytest

from velora.engines.subtitle import SceneSubtitle, StorySubtitles


def test_scene_subtitle_is_frozen() -> None:
    subtitle = SceneSubtitle(index=0, text="Hi", start_seconds=0.0, end_seconds=1.0)

    with pytest.raises(dataclasses.FrozenInstanceError):
        subtitle.text = "changed"  # type: ignore[misc]


def test_scene_subtitle_holds_its_own_text() -> None:
    subtitle = SceneSubtitle(index=2, text="The city wakes.", start_seconds=4.0, end_seconds=6.5)

    assert subtitle.index == 2
    assert subtitle.text == "The city wakes."
    assert subtitle.start_seconds == 4.0
    assert subtitle.end_seconds == 6.5


def test_story_subtitles_permits_zero_scenes() -> None:
    story_subtitles = StorySubtitles(topic="Empty", scenes=())

    assert story_subtitles.scenes == ()


def test_story_subtitles_is_frozen() -> None:
    story_subtitles = StorySubtitles(topic="A city at dawn", scenes=())

    with pytest.raises(dataclasses.FrozenInstanceError):
        story_subtitles.topic = "changed"  # type: ignore[misc]
