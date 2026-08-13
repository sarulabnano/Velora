"""Tests for velora.engines.subtitle.SubtitleEngine.

Uses real WAV bytes (constructed with the stdlib `wave` module) to
exercise the "measured from real audio" path with a known, exact
duration -- and plain non-audio bytes (the same kind of fake payload
every other test double in this suite uses for "audio") to exercise the
word-count fallback deliberately, not as a testing shortcut but as a
real behavior: mutagen genuinely can't parse those bytes, so the
fallback is what a real unparseable clip would also trigger.
"""

from __future__ import annotations

import io
import wave

import pytest

from velora.engines.narration_audio import SceneAudio, StoryAudio
from velora.engines.story import Scene, Story
from velora.engines.subtitle import SubtitleEngine


def _wav_bytes(*, seconds: float, sample_rate: int = 8000) -> bytes:
    """Build real, valid WAV audio of an exact duration."""
    frame_count = round(seconds * sample_rate)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate)
        writer.writeframes(b"\x00\x00" * frame_count)
    return buffer.getvalue()


def test_captions_every_scene_in_order() -> None:
    engine = SubtitleEngine()
    story = Story(
        topic="A day in the city",
        scenes=(
            Scene(index=0, text="The city wakes."),
            Scene(index=1, text="The market opens."),
        ),
    )
    audio = StoryAudio(
        topic="A day in the city",
        scenes=(
            SceneAudio(index=0, audio=_wav_bytes(seconds=2.0), audio_format="wav"),
            SceneAudio(index=1, audio=_wav_bytes(seconds=3.0), audio_format="wav"),
        ),
    )

    story_subtitles = engine.caption(story, audio)

    assert [s.index for s in story_subtitles.scenes] == [0, 1]
    assert [s.text for s in story_subtitles.scenes] == [
        "The city wakes.",
        "The market opens.",
    ]


def test_timing_is_measured_from_the_real_audio_duration() -> None:
    engine = SubtitleEngine()
    story = Story(topic="A day", scenes=(Scene(index=0, text="Hello there."),))
    audio = StoryAudio(
        topic="A day",
        scenes=(SceneAudio(index=0, audio=_wav_bytes(seconds=2.5), audio_format="wav"),),
    )

    story_subtitles = engine.caption(story, audio)

    assert story_subtitles.scenes[0].start_seconds == 0.0
    assert story_subtitles.scenes[0].end_seconds == pytest.approx(2.5, abs=0.01)


def test_scenes_are_captioned_back_to_back_with_no_gap() -> None:
    engine = SubtitleEngine()
    story = Story(
        topic="A day in the city",
        scenes=(Scene(index=0, text="First."), Scene(index=1, text="Second.")),
    )
    audio = StoryAudio(
        topic="A day in the city",
        scenes=(
            SceneAudio(index=0, audio=_wav_bytes(seconds=2.0), audio_format="wav"),
            SceneAudio(index=1, audio=_wav_bytes(seconds=1.5), audio_format="wav"),
        ),
    )

    story_subtitles = engine.caption(story, audio)

    first, second = story_subtitles.scenes
    assert first.start_seconds == 0.0
    assert first.end_seconds == pytest.approx(2.0, abs=0.01)
    assert second.start_seconds == pytest.approx(2.0, abs=0.01)
    assert second.end_seconds == pytest.approx(3.5, abs=0.01)


def test_topic_is_carried_over_from_the_story() -> None:
    engine = SubtitleEngine()
    story = Story(topic="The history of bridges", scenes=())
    audio = StoryAudio(topic="The history of bridges", scenes=())

    story_subtitles = engine.caption(story, audio)

    assert story_subtitles.topic == "The history of bridges"


def test_story_with_zero_scenes_produces_zero_subtitle_scenes() -> None:
    engine = SubtitleEngine()
    story = Story(topic="Nothing to say", scenes=())
    audio = StoryAudio(topic="Nothing to say", scenes=())

    story_subtitles = engine.caption(story, audio)

    assert story_subtitles.scenes == ()


def test_falls_back_to_word_count_when_audio_cannot_be_parsed() -> None:
    engine = SubtitleEngine(words_per_minute=60.0)  # 1 word/second
    story = Story(topic="A day", scenes=(Scene(index=0, text="one two three four five"),))
    audio = StoryAudio(
        topic="A day",
        # Not real audio -- mutagen can't determine a duration from this.
        scenes=(SceneAudio(index=0, audio=b"not actually audio", audio_format="mp3"),),
    )

    story_subtitles = engine.caption(story, audio)

    assert story_subtitles.scenes[0].end_seconds == pytest.approx(5.0)


def test_falls_back_to_word_count_when_no_matching_scene_audio_exists() -> None:
    engine = SubtitleEngine(words_per_minute=60.0)
    story = Story(topic="A day", scenes=(Scene(index=0, text="one two three"),))
    audio = StoryAudio(topic="A day", scenes=())  # no audio for scene 0 at all

    story_subtitles = engine.caption(story, audio)

    assert story_subtitles.scenes[0].end_seconds == pytest.approx(3.0)


def test_default_words_per_minute_is_a_reasonable_narration_pace() -> None:
    engine = SubtitleEngine()
    story = Story(
        topic="A day in the city",
        scenes=(Scene(index=0, text=" ".join(["word"] * 150)),),  # 150 words
    )
    audio = StoryAudio(
        topic="A day in the city",
        scenes=(SceneAudio(index=0, audio=b"unparseable", audio_format="mp3"),),
    )

    story_subtitles = engine.caption(story, audio)

    # 150 words at the default fallback pace should take about one minute.
    assert story_subtitles.scenes[0].end_seconds == pytest.approx(60.0)


@pytest.mark.parametrize("invalid", [0.0, -1.0, -60.0])
def test_rejects_non_positive_words_per_minute(invalid: float) -> None:
    with pytest.raises(ValueError, match="must be positive"):
        SubtitleEngine(words_per_minute=invalid)
