"""Tests for velora.providers.text_generation.AnthropicTextGenerationProvider.

No real network calls: the ``anthropic.Anthropic`` client is replaced
with a fake/mock at ``velora.providers.text_generation._anthropic.anthropic.Anthropic``.
Exceptions are constructed as real ``anthropic`` exception instances (not
generic stand-ins) so the `except` clauses in ``_anthropic.py`` are
exercised against the exact types they're written to catch.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import anthropic as anthropic_sdk
import httpx
import pytest

from velora.providers import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderRequestError,
)
from velora.providers.text_generation import (
    AnthropicTextGenerationProvider,
    Message,
    Role,
    TextGenerationRequest,
)
from velora.runtime import LifecycleComponent, RuntimeContext


def _context() -> RuntimeContext:
    return RuntimeContext(runtime_id="test-run", started_at=datetime.now(UTC))


def _fake_response(status: int) -> httpx.Response:
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return httpx.Response(status, request=request, json={"error": {"message": "boom"}})


def _fake_request() -> httpx.Request:
    return httpx.Request("POST", "https://api.anthropic.com/v1/messages")


def _fake_success_response(
    *,
    text: str = "hello",
    stop_reason: str = "end_turn",
    input_tokens: int = 10,
    output_tokens: int = 5,
) -> Any:
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.content = [block]
    response.stop_reason = stop_reason
    response.usage.input_tokens = input_tokens
    response.usage.output_tokens = output_tokens
    return response


def _basic_request() -> TextGenerationRequest:
    return TextGenerationRequest(messages=[Message(role=Role.USER, content="hi")], max_tokens=50)


# --- protocol / lifecycle conformance ------------------------------------


def test_is_recognized_as_a_lifecycle_component() -> None:
    provider = AnthropicTextGenerationProvider(api_key="k")

    assert isinstance(provider, LifecycleComponent)


def test_name_is_stable() -> None:
    provider = AnthropicTextGenerationProvider(api_key="k")

    assert provider.name == "anthropic-text-generation"


def test_generate_before_start_raises_provider_request_error() -> None:
    provider = AnthropicTextGenerationProvider(api_key="k")

    with pytest.raises(ProviderRequestError, match="before start"):
        provider.generate(_basic_request())


def test_start_constructs_the_sdk_client_with_the_given_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class _FakeClient:
        def __init__(self, api_key: str) -> None:
            captured["api_key"] = api_key
            self.messages = MagicMock()

        def close(self) -> None:
            captured["closed"] = True

    monkeypatch.setattr(anthropic_sdk, "Anthropic", _FakeClient)
    provider = AnthropicTextGenerationProvider(api_key="secret-key")

    provider.start(_context())

    assert captured["api_key"] == "secret-key"


def test_stop_closes_the_client(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    monkeypatch.setattr(anthropic_sdk, "Anthropic", lambda api_key: fake_client)
    provider = AnthropicTextGenerationProvider(api_key="k")
    provider.start(_context())

    provider.stop(_context())

    fake_client.close.assert_called_once()


def test_stop_before_start_does_not_raise() -> None:
    provider = AnthropicTextGenerationProvider(api_key="k")

    provider.stop(_context())  # must not raise


# --- request/response translation -----------------------------------------


def test_generate_translates_request_and_response(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_success_response(
        text="hi there", input_tokens=7, output_tokens=3
    )
    monkeypatch.setattr(anthropic_sdk, "Anthropic", lambda api_key: fake_client)
    provider = AnthropicTextGenerationProvider(api_key="k")
    provider.start(_context())

    request = TextGenerationRequest(
        messages=[Message(role=Role.USER, content="hi")],
        max_tokens=50,
        system="be nice",
        temperature=0.5,
    )
    result = provider.generate(request)

    assert result.text == "hi there"
    assert result.stop_reason == "end_turn"
    assert result.input_tokens == 7
    assert result.output_tokens == 3

    call_kwargs = fake_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-sonnet-5"
    assert call_kwargs["max_tokens"] == 50
    assert call_kwargs["system"] == "be nice"
    assert call_kwargs["temperature"] == 0.5
    assert call_kwargs["messages"] == [{"role": "user", "content": "hi"}]


def test_generate_omits_system_and_temperature_when_not_given(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_success_response()
    monkeypatch.setattr(anthropic_sdk, "Anthropic", lambda api_key: fake_client)
    provider = AnthropicTextGenerationProvider(api_key="k")
    provider.start(_context())

    provider.generate(_basic_request())

    call_kwargs = fake_client.messages.create.call_args.kwargs
    assert "system" not in call_kwargs
    assert "temperature" not in call_kwargs


def test_custom_model_overrides_the_default(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_success_response()
    monkeypatch.setattr(anthropic_sdk, "Anthropic", lambda api_key: fake_client)
    provider = AnthropicTextGenerationProvider(api_key="k", model="claude-haiku-4-5-20251001")
    provider.start(_context())

    provider.generate(_basic_request())

    assert fake_client.messages.create.call_args.kwargs["model"] == "claude-haiku-4-5-20251001"


def test_multiple_text_blocks_are_concatenated(monkeypatch: pytest.MonkeyPatch) -> None:
    block_a = MagicMock(type="text", text="Hello, ")
    block_b = MagicMock(type="text", text="world.")
    response = MagicMock()
    response.content = [block_a, block_b]
    response.stop_reason = "end_turn"
    response.usage.input_tokens = 1
    response.usage.output_tokens = 1
    fake_client = MagicMock()
    fake_client.messages.create.return_value = response
    monkeypatch.setattr(anthropic_sdk, "Anthropic", lambda api_key: fake_client)
    provider = AnthropicTextGenerationProvider(api_key="k")
    provider.start(_context())

    result = provider.generate(_basic_request())

    assert result.text == "Hello, world."


def test_missing_stop_reason_defaults_to_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _fake_success_response()
    response.stop_reason = None
    fake_client = MagicMock()
    fake_client.messages.create.return_value = response
    monkeypatch.setattr(anthropic_sdk, "Anthropic", lambda api_key: fake_client)
    provider = AnthropicTextGenerationProvider(api_key="k")
    provider.start(_context())

    result = provider.generate(_basic_request())

    assert result.stop_reason == "unknown"


# --- error translation -------------------------------------------------------


def test_authentication_error_is_translated(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_client.messages.create.side_effect = anthropic_sdk.AuthenticationError(
        "invalid key", response=_fake_response(401), body=None
    )
    monkeypatch.setattr(anthropic_sdk, "Anthropic", lambda api_key: fake_client)
    provider = AnthropicTextGenerationProvider(api_key="bad-key")
    provider.start(_context())

    with pytest.raises(ProviderAuthenticationError):
        provider.generate(_basic_request())


def test_rate_limit_error_is_translated(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_client.messages.create.side_effect = anthropic_sdk.RateLimitError(
        "too many requests", response=_fake_response(429), body=None
    )
    monkeypatch.setattr(anthropic_sdk, "Anthropic", lambda api_key: fake_client)
    provider = AnthropicTextGenerationProvider(api_key="k")
    provider.start(_context())

    with pytest.raises(ProviderRateLimitError):
        provider.generate(_basic_request())


def test_connection_error_is_translated(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_client.messages.create.side_effect = anthropic_sdk.APIConnectionError(
        message="network down", request=_fake_request()
    )
    monkeypatch.setattr(anthropic_sdk, "Anthropic", lambda api_key: fake_client)
    provider = AnthropicTextGenerationProvider(api_key="k")
    provider.start(_context())

    with pytest.raises(ProviderConnectionError):
        provider.generate(_basic_request())


def test_generic_api_status_error_is_translated(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_client.messages.create.side_effect = anthropic_sdk.APIStatusError(
        "server error", response=_fake_response(500), body=None
    )
    monkeypatch.setattr(anthropic_sdk, "Anthropic", lambda api_key: fake_client)
    provider = AnthropicTextGenerationProvider(api_key="k")
    provider.start(_context())

    with pytest.raises(ProviderRequestError):
        provider.generate(_basic_request())


def test_bad_request_error_is_translated_as_a_request_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """BadRequestError is a subclass of APIStatusError: caught by the same clause."""
    fake_client = MagicMock()
    fake_client.messages.create.side_effect = anthropic_sdk.BadRequestError(
        "malformed request", response=_fake_response(400), body=None
    )
    monkeypatch.setattr(anthropic_sdk, "Anthropic", lambda api_key: fake_client)
    provider = AnthropicTextGenerationProvider(api_key="k")
    provider.start(_context())

    with pytest.raises(ProviderRequestError):
        provider.generate(_basic_request())
