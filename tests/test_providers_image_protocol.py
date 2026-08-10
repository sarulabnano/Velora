"""Tests for velora.providers.image.ImageProvider."""

from __future__ import annotations

from velora.providers.image import ImageProvider, ImageRequest, ImageResult


class _FakeProvider:
    def generate(self, request: ImageRequest) -> ImageResult:
        del request
        return ImageResult(image=b"fake-image", image_format="png")


def test_conforming_object_is_recognized_as_an_image_provider() -> None:
    assert isinstance(_FakeProvider(), ImageProvider)


def test_object_without_generate_is_not_an_image_provider() -> None:
    assert not isinstance(object(), ImageProvider)


def test_fake_provider_is_directly_callable() -> None:
    provider = _FakeProvider()
    request = ImageRequest(prompt="a cat")

    result = provider.generate(request)

    assert result.image == b"fake-image"
