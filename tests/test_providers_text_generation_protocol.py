"""Tests for velora.providers.text_generation.TextGenerationProvider."""

from __future__ import annotations

from velora.providers.text_generation import (
    Message,
    Role,
    TextGenerationProvider,
    TextGenerationRequest,
    TextGenerationResult,
)


class _FakeProvider:
    def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
        del request
        return TextGenerationResult(
            text="fake", stop_reason="end_turn", input_tokens=1, output_tokens=1
        )


def test_conforming_object_is_recognized_as_a_text_generation_provider() -> None:
    assert isinstance(_FakeProvider(), TextGenerationProvider)


def test_object_without_generate_is_not_a_text_generation_provider() -> None:
    assert not isinstance(object(), TextGenerationProvider)


def test_fake_provider_is_directly_callable() -> None:
    provider = _FakeProvider()
    request = TextGenerationRequest(messages=[Message(role=Role.USER, content="hi")], max_tokens=10)

    result = provider.generate(request)

    assert result.text == "fake"
