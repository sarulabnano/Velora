"""Tests for velora.providers.voice.ElevenLabsVoiceProvider.

No real network calls: the ``elevenlabs.ElevenLabs`` client is replaced
with a fake at ``velora.providers.voice._elevenlabs.elevenlabs.ElevenLabs``.
Exceptions are constructed as real ``elevenlabs``/``httpx`` exception
instances (not generic stand-ins) so the `except` clauses in
``_elevenlabs.py`` are exercised against the exact types they're written
to catch.

``text_to_speech.convert()`` is itself a generator in the real SDK: the
HTTP call only happens once its return value is iterated (here, inside
``b"".join(...)``), not at call time. Setting ``side_effect`` directly
on the mocked ``convert`` (raising immediately on call, rather than on
first iteration) is a faithful enough stand-in for these tests: what's
under test is `_elevenlabs.py`'s own translation logic, and its ``try``
block already wraps both the call and the join.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import elevenlabs as elevenlabs_sdk
import httpx
import pytest

from velora.providers import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderRequestError,
)
from velora.providers.voice import ElevenLabsVoiceProvider, SpeechRequest
from velora.runtime import LifecycleComponent, RuntimeContext


def _context() -> RuntimeContext:
    return RuntimeContext(runtime_id="test-run", started_at=datetime.now(UTC))


def _fake_client_with_audio(chunks: list[bytes]) -> MagicMock:
    fake_client = MagicMock()
    fake_client.text_to_speech.convert.return_value = iter(chunks)
    return fake_client


# --- protocol / lifecycle conformance ------------------------------------


def test_is_recognized_as_a_lifecycle_component() -> None:
    provider = ElevenLabsVoiceProvider(api_key="k")

    assert isinstance(provider, LifecycleComponent)


def test_name_is_stable() -> None:
    provider = ElevenLabsVoiceProvider(api_key="k")

    assert provider.name == "elevenlabs-voice"


def test_synthesize_before_start_raises_provider_request_error() -> None:
    provider = ElevenLabsVoiceProvider(api_key="k")

    with pytest.raises(ProviderRequestError, match="before start"):
        provider.synthesize(SpeechRequest(text="hi"))


def test_start_constructs_the_sdk_client_with_the_given_api_key_and_an_httpx_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class _FakeClient:
        def __init__(self, *, api_key: str, httpx_client: httpx.Client) -> None:
            captured["api_key"] = api_key
            captured["httpx_client"] = httpx_client
            self.text_to_speech = MagicMock()

    monkeypatch.setattr(elevenlabs_sdk, "ElevenLabs", _FakeClient)
    provider = ElevenLabsVoiceProvider(api_key="secret-key")

    provider.start(_context())

    assert captured["api_key"] == "secret-key"
    assert isinstance(captured["httpx_client"], httpx.Client)


def test_stop_closes_the_injected_http_client(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_http_client = MagicMock()
    monkeypatch.setattr(httpx, "Client", lambda: fake_http_client)
    monkeypatch.setattr(elevenlabs_sdk, "ElevenLabs", lambda *, api_key, httpx_client: MagicMock())
    provider = ElevenLabsVoiceProvider(api_key="k")
    provider.start(_context())

    provider.stop(_context())

    fake_http_client.close.assert_called_once()


def test_stop_before_start_does_not_raise() -> None:
    provider = ElevenLabsVoiceProvider(api_key="k")

    provider.stop(_context())  # must not raise


# --- request/response translation -----------------------------------------


def test_synthesize_joins_audio_chunks_into_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = _fake_client_with_audio([b"abc", b"def"])
    monkeypatch.setattr(elevenlabs_sdk, "ElevenLabs", lambda *, api_key, httpx_client: fake_client)
    provider = ElevenLabsVoiceProvider(api_key="k")
    provider.start(_context())

    result = provider.synthesize(SpeechRequest(text="hello"))

    assert result.audio == b"abcdef"
    assert result.audio_format == "mp3"


def test_synthesize_passes_text_and_the_default_voice_and_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = _fake_client_with_audio([b"a"])
    monkeypatch.setattr(elevenlabs_sdk, "ElevenLabs", lambda *, api_key, httpx_client: fake_client)
    provider = ElevenLabsVoiceProvider(api_key="k")
    provider.start(_context())

    provider.synthesize(SpeechRequest(text="hello world"))

    call = fake_client.text_to_speech.convert.call_args
    assert call.args[0] == "21m00Tcm4TlvDq8ikWAM"
    assert call.kwargs["text"] == "hello world"
    assert call.kwargs["model_id"] == "eleven_multilingual_v2"


def test_custom_voice_and_model_override_the_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = _fake_client_with_audio([b"a"])
    monkeypatch.setattr(elevenlabs_sdk, "ElevenLabs", lambda *, api_key, httpx_client: fake_client)
    provider = ElevenLabsVoiceProvider(
        api_key="k", voice_id="custom-voice", model_id="custom-model"
    )
    provider.start(_context())

    provider.synthesize(SpeechRequest(text="hi"))

    call = fake_client.text_to_speech.convert.call_args
    assert call.args[0] == "custom-voice"
    assert call.kwargs["model_id"] == "custom-model"


# --- error translation -------------------------------------------------------


def test_unprocessable_entity_is_translated_as_a_request_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = MagicMock()
    fake_client.text_to_speech.convert.side_effect = elevenlabs_sdk.errors.UnprocessableEntityError(
        body={"detail": "bad request"}
    )
    monkeypatch.setattr(elevenlabs_sdk, "ElevenLabs", lambda *, api_key, httpx_client: fake_client)
    provider = ElevenLabsVoiceProvider(api_key="k")
    provider.start(_context())

    with pytest.raises(ProviderRequestError):
        provider.synthesize(SpeechRequest(text="hi"))


def test_unauthorized_api_error_is_translated_as_authentication_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = MagicMock()
    fake_client.text_to_speech.convert.side_effect = elevenlabs_sdk.core.ApiError(
        status_code=401, body={"detail": "unauthorized"}
    )
    monkeypatch.setattr(elevenlabs_sdk, "ElevenLabs", lambda *, api_key, httpx_client: fake_client)
    provider = ElevenLabsVoiceProvider(api_key="bad-key")
    provider.start(_context())

    with pytest.raises(ProviderAuthenticationError):
        provider.synthesize(SpeechRequest(text="hi"))


def test_rate_limited_api_error_is_translated_as_rate_limit_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = MagicMock()
    fake_client.text_to_speech.convert.side_effect = elevenlabs_sdk.core.ApiError(
        status_code=429, body={"detail": "slow down"}
    )
    monkeypatch.setattr(elevenlabs_sdk, "ElevenLabs", lambda *, api_key, httpx_client: fake_client)
    provider = ElevenLabsVoiceProvider(api_key="k")
    provider.start(_context())

    with pytest.raises(ProviderRateLimitError):
        provider.synthesize(SpeechRequest(text="hi"))


def test_other_api_error_is_translated_as_a_request_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = MagicMock()
    fake_client.text_to_speech.convert.side_effect = elevenlabs_sdk.core.ApiError(
        status_code=500, body={"detail": "server error"}
    )
    monkeypatch.setattr(elevenlabs_sdk, "ElevenLabs", lambda *, api_key, httpx_client: fake_client)
    provider = ElevenLabsVoiceProvider(api_key="k")
    provider.start(_context())

    with pytest.raises(ProviderRequestError):
        provider.synthesize(SpeechRequest(text="hi"))


def test_connection_error_is_translated(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = MagicMock()
    fake_client.text_to_speech.convert.side_effect = httpx.ConnectError("network down")
    monkeypatch.setattr(elevenlabs_sdk, "ElevenLabs", lambda *, api_key, httpx_client: fake_client)
    provider = ElevenLabsVoiceProvider(api_key="k")
    provider.start(_context())

    with pytest.raises(ProviderConnectionError):
        provider.synthesize(SpeechRequest(text="hi"))
