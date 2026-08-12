"""Tests for velora.engines.subtitle.render_srt."""

from __future__ import annotations

from velora.engines.subtitle import SceneSubtitle, StorySubtitles, render_srt


def test_renders_one_numbered_block_per_scene() -> None:
    subtitles = StorySubtitles(
        topic="A day in the city",
        scenes=(
            SceneSubtitle(index=0, text="The city wakes.", start_seconds=0.0, end_seconds=2.5),
            SceneSubtitle(index=1, text="The market opens.", start_seconds=2.5, end_seconds=5.0),
        ),
    )

    srt = render_srt(subtitles)

    assert srt == (
        "1\n"
        "00:00:00,000 --> 00:00:02,500\n"
        "The city wakes.\n"
        "\n"
        "2\n"
        "00:00:02,500 --> 00:00:05,000\n"
        "The market opens.\n"
    )


def test_cue_numbers_are_one_based_regardless_of_scene_index() -> None:
    subtitles = StorySubtitles(
        topic="A day in the city",
        scenes=(SceneSubtitle(index=7, text="Only scene.", start_seconds=0.0, end_seconds=1.0),),
    )

    srt = render_srt(subtitles)

    assert srt.startswith("1\n")


def test_renders_empty_string_for_zero_scenes() -> None:
    subtitles = StorySubtitles(topic="Nothing to say", scenes=())

    assert render_srt(subtitles) == ""


def test_timestamps_beyond_an_hour_are_formatted_correctly() -> None:
    subtitles = StorySubtitles(
        topic="A very long story",
        scenes=(
            SceneSubtitle(index=0, text="Long scene.", start_seconds=3725.125, end_seconds=3730.0),
        ),
    )

    srt = render_srt(subtitles)

    assert "01:02:05,125 --> 01:02:10,000" in srt
