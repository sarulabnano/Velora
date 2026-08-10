"""Tests for velora.services.image.ImageService.

Uses a fake ImageProvider throughout -- never OpenAIImageProvider --
to make the architectural point explicit: ImageService works
identically regardless of which concrete Provider answers
(docs/VISION.md, ADR-0008).
"""

from __future__ import annotations

import pytest

from velora.providers.image import ImageRequest, ImageResult
from velora.services.image import ImageService


class _FakeProvider:
    def __init__(self, result: ImageResult) -> None:
        self._result = result
        self.received_requests: list[ImageRequest] = []

    def generate(self, request: ImageRequest) -> ImageResult:
        self.received_requests.append(request)
        return self._result


def _fake_result(image: bytes = b"fake-image") -> ImageResult:
    return ImageResult(image=image, image_format="png")


def test_draw_returns_the_providers_result() -> None:
    provider = _FakeProvider(_fake_result(b"the-actual-image"))
    service = ImageService(provider)

    result = service.draw("a cat wearing a hat")

    assert result.image == b"the-actual-image"


def test_draw_sends_prompt_to_the_provider() -> None:
    provider = _FakeProvider(_fake_result())
    service = ImageService(provider)

    service.draw("a sunrise over the mountains")

    sent = provider.received_requests[0]
    assert sent.prompt == "a sunrise over the mountains"


@pytest.mark.parametrize("blank", ["", "   ", "\n\t"])
def test_draw_rejects_empty_prompt(blank: str) -> None:
    provider = _FakeProvider(_fake_result())
    service = ImageService(provider)

    with pytest.raises(ValueError, match="must not be empty"):
        service.draw(blank)


def test_draw_does_not_call_the_provider_when_prompt_is_empty() -> None:
    provider = _FakeProvider(_fake_result())
    service = ImageService(provider)

    with pytest.raises(ValueError):
        service.draw("")

    assert provider.received_requests == []


def test_service_works_identically_with_any_conforming_provider() -> None:
    """The whole point of the contract: swap the provider, nothing else changes."""

    class _AnotherFakeProvider:
        def generate(self, request: ImageRequest) -> ImageResult:
            del request
            return _fake_result(b"a-completely-different-backend-answered")

    service = ImageService(_AnotherFakeProvider())

    result = service.draw("Anything.")

    assert result.image == b"a-completely-different-backend-answered"
