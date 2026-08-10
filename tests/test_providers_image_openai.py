"""Tests for velora.providers.image.OpenAIImageProvider.

No real network calls: the ``openai.OpenAI`` client is replaced with a
fake/mock at ``velora.providers.image._openai.openai.OpenAI``.
Exceptions are constructed as real ``openai`` exception instances (not
generic stand-ins) so the `except` clauses in ``_openai.py`` are
exercised against the exact types they're written to catch -- same
testing philosophy ``test_providers_text_generation_anthropic.py``
already established (ADR-0009), since the ``openai`` SDK's own
exception hierarchy mirrors ``anthropic``'s almost exactly.
"""

from __future__ import annotations

import base64
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import httpx
import openai as openai_sdk
import pytest

from velora.providers import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderRequestError,
)
from velora.providers.image import ImageRequest, OpenAIImageProvider
from velora.runtime import LifecycleComponent, RuntimeContext


def _context() -> RuntimeContext:
    return RuntimeContext(runtime_id="test-run", started_at=datetime.now(UTC))


def _fake_response(status: int) -> httpx.Response:
    request = httpx.Request("POST", "https://api.openai.com/v1/images/generations")
    return httpx.Response(status, request=request, json={"error": {"message": "boom"}})


def _fake_request() -> httpx.Request:
    return httpx.Request("POST", "https://api.openai.com/v1/images/generations")


def _fake_success_response(b64_json: str | None = "ZmFrZS1pbWFnZQ==") -> Any:
    image = MagicMock()
    image.b64_json = b64_json
    response = MagicMock()
    response.data = [image]
    return response


def _basic_request() -> ImageRequest:
    return ImageRequest(prompt="a cat wearing a hat")


# --- protocol / lifecycle conformance ------------------------------------


def test_is_recognized_as_a_lifecycle_component() -> None:
    provider = OpenAIImageProvider(api_key="k")

    assert isinstance(provider, LifecycleComponent)


def test_name_is_stable() -> None:
    provider = OpenAIImageProvider(api_key="k")

    assert provider.name == "openai-image"


def test_generate_before_start_raises_provider_request_error() -> None:
    provider = OpenAIImageProvider(api_key="k")

    with pytest.raises(ProviderRequestError, match="before start"):
        provider.generate(_basic_request())


def test_start_constructs_the_sdk_client_with_the_given_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class _FakeClient:
        def __init__(self, *, api_key: str, http_client: object) -> None:
            captured["api_key"] = api_key
            captured["http_client"] = http_client
            self.images = MagicMock()

    monkeypatch.setattr(openai_sdk, "OpenAI", _FakeClient)
    provider = OpenAIImageProvider(api_key="secret-key")

    provider.start(_context())

    assert captured["api_key"] == "secret-key"
    assert isinstance(captured["http_client"], httpx.Client)


def test_stop_closes_the_http_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        openai_sdk, "OpenAI", lambda *, api_key, http_client: MagicMock(images=MagicMock())
    )
    provider = OpenAIImageProvider(api_key="k")
    provider.start(_context())
    http_client = provider._http_client
    assert http_client is not None

    provider.stop(_context())

    assert http_client.is_closed


def test_stop_before_start_does_not_raise() -> None:
    provider = OpenAIImageProvider(api_key="k")

    provider.stop(_context())  # must not raise


# --- request/response translation -----------------------------------------


def test_generate_translates_request_and_response(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_client.images.generate.return_value = _fake_success_response(
        base64.b64encode(b"the-actual-image-bytes").decode()
    )
    monkeypatch.setattr(openai_sdk, "OpenAI", lambda *, api_key, http_client: fake_client)
    provider = OpenAIImageProvider(api_key="k")
    provider.start(_context())

    result = provider.generate(ImageRequest(prompt="a cat wearing a hat"))

    assert result.image == b"the-actual-image-bytes"
    assert result.image_format == "png"

    call_kwargs = fake_client.images.generate.call_args.kwargs
    assert call_kwargs["model"] == "dall-e-3"
    assert call_kwargs["prompt"] == "a cat wearing a hat"
    assert call_kwargs["size"] == "1024x1024"
    assert call_kwargs["n"] == 1
    assert call_kwargs["response_format"] == "b64_json"


def test_custom_model_and_size_override_the_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_client.images.generate.return_value = _fake_success_response()
    monkeypatch.setattr(openai_sdk, "OpenAI", lambda *, api_key, http_client: fake_client)
    provider = OpenAIImageProvider(api_key="k", model="dall-e-2", size="512x512")
    provider.start(_context())

    provider.generate(_basic_request())

    call_kwargs = fake_client.images.generate.call_args.kwargs
    assert call_kwargs["model"] == "dall-e-2"
    assert call_kwargs["size"] == "512x512"


def test_missing_response_data_raises_provider_request_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = MagicMock()
    response = MagicMock()
    response.data = []
    fake_client.images.generate.return_value = response
    monkeypatch.setattr(openai_sdk, "OpenAI", lambda *, api_key, http_client: fake_client)
    provider = OpenAIImageProvider(api_key="k")
    provider.start(_context())

    with pytest.raises(ProviderRequestError, match="no image data"):
        provider.generate(_basic_request())


def test_missing_b64_json_raises_provider_request_error(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_client.images.generate.return_value = _fake_success_response(b64_json=None)
    monkeypatch.setattr(openai_sdk, "OpenAI", lambda *, api_key, http_client: fake_client)
    provider = OpenAIImageProvider(api_key="k")
    provider.start(_context())

    with pytest.raises(ProviderRequestError, match="no image data"):
        provider.generate(_basic_request())


# --- error translation -------------------------------------------------------


def test_authentication_error_is_translated(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_client.images.generate.side_effect = openai_sdk.AuthenticationError(
        "invalid key", response=_fake_response(401), body=None
    )
    monkeypatch.setattr(openai_sdk, "OpenAI", lambda *, api_key, http_client: fake_client)
    provider = OpenAIImageProvider(api_key="bad-key")
    provider.start(_context())

    with pytest.raises(ProviderAuthenticationError):
        provider.generate(_basic_request())


def test_rate_limit_error_is_translated(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_client.images.generate.side_effect = openai_sdk.RateLimitError(
        "too many requests", response=_fake_response(429), body=None
    )
    monkeypatch.setattr(openai_sdk, "OpenAI", lambda *, api_key, http_client: fake_client)
    provider = OpenAIImageProvider(api_key="k")
    provider.start(_context())

    with pytest.raises(ProviderRateLimitError):
        provider.generate(_basic_request())


def test_connection_error_is_translated(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_client.images.generate.side_effect = openai_sdk.APIConnectionError(
        message="network down", request=_fake_request()
    )
    monkeypatch.setattr(openai_sdk, "OpenAI", lambda *, api_key, http_client: fake_client)
    provider = OpenAIImageProvider(api_key="k")
    provider.start(_context())

    with pytest.raises(ProviderConnectionError):
        provider.generate(_basic_request())


def test_generic_api_status_error_is_translated(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_client.images.generate.side_effect = openai_sdk.APIStatusError(
        "server error", response=_fake_response(500), body=None
    )
    monkeypatch.setattr(openai_sdk, "OpenAI", lambda *, api_key, http_client: fake_client)
    provider = OpenAIImageProvider(api_key="k")
    provider.start(_context())

    with pytest.raises(ProviderRequestError):
        provider.generate(_basic_request())


def test_bad_request_error_is_translated_as_a_request_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """BadRequestError is a subclass of APIStatusError: caught by the same clause."""
    fake_client = MagicMock()
    fake_client.images.generate.side_effect = openai_sdk.BadRequestError(
        "malformed request", response=_fake_response(400), body=None
    )
    monkeypatch.setattr(openai_sdk, "OpenAI", lambda *, api_key, http_client: fake_client)
    provider = OpenAIImageProvider(api_key="k")
    provider.start(_context())

    with pytest.raises(ProviderRequestError):
        provider.generate(_basic_request())
