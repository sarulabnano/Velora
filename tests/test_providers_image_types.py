"""Tests for velora.providers.image type shapes."""

from __future__ import annotations

import dataclasses

import pytest

from velora.providers.image import ImageRequest, ImageResult


def test_image_request_is_frozen() -> None:
    request = ImageRequest(prompt="a cat")

    with pytest.raises(dataclasses.FrozenInstanceError):
        request.prompt = "changed"  # type: ignore[misc]


def test_image_result_is_frozen() -> None:
    result = ImageResult(image=b"\x00", image_format="png")

    with pytest.raises(dataclasses.FrozenInstanceError):
        result.image_format = "jpeg"  # type: ignore[misc]


def test_image_result_holds_the_given_image_bytes_and_format() -> None:
    result = ImageResult(image=b"some-bytes", image_format="png")

    assert result.image == b"some-bytes"
    assert result.image_format == "png"
