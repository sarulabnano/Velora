"""Tests for velora.engines.scene_image.SceneImageEngine.

Uses a real ImageService, with a fake ImageProvider -- the only faked
boundary is the actual external call. This exercises the real
SceneImageEngine -> ImageService integration, not a mocked stand-in for
ImageService itself.
"""

from __future__ import annotations

import pytest

from velora.engines.scene_image import SceneImageEngine
from velora.engines.story import Scene, Story
from velora.providers import ProviderRequestError
from velora.providers.image import ImageRequest, ImageResult
from velora.services.image import ImageService


class _FakeProvider:
    def __init__(self) -> None:
        self.received_requests: list[ImageRequest] = []

    def generate(self, request: ImageRequest) -> ImageResult:
        self.received_requests.append(request)
        image = request.prompt.encode()
        return ImageResult(image=image, image_format="png")


class _FailingProvider:
    def generate(self, request: ImageRequest) -> ImageResult:
        del request
        raise ProviderRequestError("generation failed")


def _engine() -> tuple[SceneImageEngine, _FakeProvider]:
    provider = _FakeProvider()
    engine = SceneImageEngine(ImageService(provider))
    return engine, provider


def test_illustrates_every_scene_in_order() -> None:
    engine, _ = _engine()
    story = Story(
        topic="A day in the city",
        scenes=(
            Scene(index=0, text="The city wakes."),
            Scene(index=1, text="The market opens."),
        ),
    )

    story_images = engine.illustrate(story)

    assert [s.image for s in story_images.scenes] == [b"The city wakes.", b"The market opens."]
    assert [s.index for s in story_images.scenes] == [0, 1]
    assert [s.image_format for s in story_images.scenes] == ["png", "png"]


def test_topic_is_carried_over_from_the_story() -> None:
    engine, _ = _engine()
    story = Story(topic="The history of bridges", scenes=())

    story_images = engine.illustrate(story)

    assert story_images.topic == "The history of bridges"


def test_story_with_zero_scenes_produces_zero_scene_images_not_an_error() -> None:
    engine, provider = _engine()
    story = Story(topic="Nothing to say", scenes=())

    story_images = engine.illustrate(story)

    assert story_images.scenes == ()
    assert provider.received_requests == []


def test_each_scenes_text_is_sent_to_the_image_service_as_the_prompt() -> None:
    engine, provider = _engine()
    story = Story(
        topic="A day in the city",
        scenes=(Scene(index=0, text="First scene."), Scene(index=1, text="Second scene.")),
    )

    engine.illustrate(story)

    assert [r.prompt for r in provider.received_requests] == ["First scene.", "Second scene."]


def test_a_failing_scene_stops_illustration_and_propagates() -> None:
    engine = SceneImageEngine(ImageService(_FailingProvider()))
    story = Story(
        topic="A day in the city",
        scenes=(Scene(index=0, text="First scene."), Scene(index=1, text="Second scene.")),
    )

    with pytest.raises(ProviderRequestError):
        engine.illustrate(story)


def test_works_identically_with_any_conforming_provider() -> None:
    """The architectural point: swap the Provider behind ImageService,
    SceneImageEngine behaves identically -- it never sees the Provider
    at all."""

    class _AnotherFakeProvider:
        def generate(self, request: ImageRequest) -> ImageResult:
            del request
            return ImageResult(image=b"a-completely-different-backend", image_format="webp")

    engine = SceneImageEngine(ImageService(_AnotherFakeProvider()))
    story = Story(topic="Anything", scenes=(Scene(index=0, text="Hi"),))

    story_images = engine.illustrate(story)

    assert story_images.scenes[0].image == b"a-completely-different-backend"
    assert story_images.scenes[0].image_format == "webp"
