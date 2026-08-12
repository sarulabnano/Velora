"""Tests for velora.engines.subtitle.SubtitleEngine."""

from __future__ import annotations

import pytest

from velora.engines.story import Scene, Story
from velora.engines.subtitle import SubtitleEngine


def test_captions_every_scene_in_order() -> None:
    engine = SubtitleEngine(words_per_minute=60.0)  # 1 word/second, easy to reason about
    story = Story(
        topic="A day in the city",
        scenes=(
            Scene(index=0, text="one two three four five"),  # 5 words -> 5s
            Scene(index=1, text="six seven"),  # 2 words -> 2s
        ),
    )

    story_subtitles = engine.caption(story)

    assert [s.index for s in story_subtitles.scenes] == [0, 1]
    assert [s.text for s in story_subtitles.scenes] == [
        "one two three four five",
        "six seven",
    ]


def test_scenes_are_captioned_back_to_back_with_no_gap() -> None:
    engine = SubtitleEngine(words_per_minute=60.0)
    story = Story(
        topic="A day in the city",
        scenes=(
            Scene(index=0, text="one two three four five"),  # 5s
            Scene(index=1, text="six seven"),  # 2s
        ),
    )

    story_subtitles = engine.caption(story)

    first, second = story_subtitles.scenes
    assert first.start_seconds == 0.0
    assert first.end_seconds == pytest.approx(5.0)
    assert second.start_seconds == pytest.approx(5.0)
    assert second.end_seconds == pytest.approx(7.0)


def test_topic_is_carried_over_from_the_story() -> None:
    engine = SubtitleEngine()
    story = Story(topic="The history of bridges", scenes=())

    story_subtitles = engine.caption(story)

    assert story_subtitles.topic == "The history of bridges"


def test_story_with_zero_scenes_produces_zero_subtitle_scenes() -> None:
    engine = SubtitleEngine()
    story = Story(topic="Nothing to say", scenes=())

    story_subtitles = engine.caption(story)

    assert story_subtitles.scenes == ()


def test_a_higher_words_per_minute_produces_shorter_durations() -> None:
    story = Story(
        topic="A day in the city",
        scenes=(Scene(index=0, text="one two three four five six"),),
    )

    slow = SubtitleEngine(words_per_minute=60.0).caption(story)
    fast = SubtitleEngine(words_per_minute=120.0).caption(story)

    assert slow.scenes[0].end_seconds > fast.scenes[0].end_seconds


def test_default_words_per_minute_is_a_reasonable_narration_pace() -> None:
    engine = SubtitleEngine()
    story = Story(
        topic="A day in the city",
        scenes=(Scene(index=0, text=" ".join(["word"] * 150)),),  # 150 words
    )

    story_subtitles = engine.caption(story)

    # 150 words at the default pace should take about one minute.
    assert story_subtitles.scenes[0].end_seconds == pytest.approx(60.0)


@pytest.mark.parametrize("invalid", [0.0, -1.0, -60.0])
def test_rejects_non_positive_words_per_minute(invalid: float) -> None:
    with pytest.raises(ValueError, match="must be positive"):
        SubtitleEngine(words_per_minute=invalid)
