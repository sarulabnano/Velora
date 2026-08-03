"""Tests for velora.services.narration.NarrationService.

Uses a fake TextGenerationProvider throughout — never
AnthropicTextGenerationProvider — to make the architectural point
explicit: NarrationService works identically regardless of which
concrete Provider answers (docs/VISION.md, ADR-0008).
"""

from __future__ import annotations

import pytest

from velora.providers.text_generation import (
    TextGenerationRequest,
    TextGenerationResult,
)
from velora.services.narration import NarrationService


class _FakeProvider:
    def __init__(self, result: TextGenerationResult) -> None:
        self._result = result
        self.received_requests: list[TextGenerationRequest] = []

    def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
        self.received_requests.append(request)
        return self._result


def _fake_result(text: str = "Once upon a time...") -> TextGenerationResult:
    return TextGenerationResult(text=text, stop_reason="end_turn", input_tokens=10, output_tokens=5)


def test_narrate_returns_the_providers_result() -> None:
    provider = _FakeProvider(_fake_result("The city never sleeps."))
    service = NarrationService(provider)

    result = service.narrate("Write about a city at night.")

    assert result.text == "The city never sleeps."


def test_narrate_sends_instructions_as_the_user_message() -> None:
    provider = _FakeProvider(_fake_result())
    service = NarrationService(provider)

    service.narrate("Describe a sunrise over the mountains.")

    sent = provider.received_requests[0]
    assert len(sent.messages) == 1
    assert sent.messages[0].content == "Describe a sunrise over the mountains."


def test_narrate_includes_a_system_prompt_by_default() -> None:
    provider = _FakeProvider(_fake_result())
    service = NarrationService(provider)

    service.narrate("Describe the ocean.")

    assert provider.received_requests[0].system is not None


def test_narrate_accepts_a_custom_system_prompt() -> None:
    provider = _FakeProvider(_fake_result())
    service = NarrationService(provider, system_prompt="Write like a pirate.")

    service.narrate("Describe the ocean.")

    assert provider.received_requests[0].system == "Write like a pirate."


def test_narrate_passes_max_tokens_through() -> None:
    provider = _FakeProvider(_fake_result())
    service = NarrationService(provider)

    service.narrate("Describe a forest.", max_tokens=42)

    assert provider.received_requests[0].max_tokens == 42


def test_narrate_defaults_max_tokens_to_1024() -> None:
    provider = _FakeProvider(_fake_result())
    service = NarrationService(provider)

    service.narrate("Describe a forest.")

    assert provider.received_requests[0].max_tokens == 1024


@pytest.mark.parametrize("blank", ["", "   ", "\n\t"])
def test_narrate_rejects_empty_instructions(blank: str) -> None:
    provider = _FakeProvider(_fake_result())
    service = NarrationService(provider)

    with pytest.raises(ValueError, match="must not be empty"):
        service.narrate(blank)


def test_narrate_does_not_call_the_provider_when_instructions_are_empty() -> None:
    provider = _FakeProvider(_fake_result())
    service = NarrationService(provider)

    with pytest.raises(ValueError):
        service.narrate("")

    assert provider.received_requests == []


def test_service_works_identically_with_any_conforming_provider() -> None:
    """The whole point of the contract: swap the provider, nothing else changes."""

    class _AnotherFakeProvider:
        def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
            del request
            return _fake_result("A completely different backend answered.")

    service = NarrationService(_AnotherFakeProvider())

    result = service.narrate("Describe anything.")

    assert result.text == "A completely different backend answered."
