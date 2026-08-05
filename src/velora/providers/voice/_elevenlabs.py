"""VoiceProvider backed by the ElevenLabs Text-to-Speech API.

Contains no business logic — only translation between the generic
``SpeechRequest``/``SpeechResult`` contract and the ``elevenlabs`` SDK's
own request/response shapes and exceptions.

Requires the ``elevenlabs`` package (the ``velora[elevenlabs]`` extra).
Importing this module without it installed raises ``ImportError`` with
that guidance, rather than a bare ``ModuleNotFoundError`` — same pattern
``_anthropic.py`` already established: no other Provider needs it, so
it is never a required dependency of ``velora`` itself.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from velora.providers._errors import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderRequestError,
)
from velora.providers.voice._types import SpeechResult

if TYPE_CHECKING:
    from velora.providers.voice._types import SpeechRequest
    from velora.runtime import RuntimeContext

try:
    import elevenlabs
    import elevenlabs.core
    import elevenlabs.errors
    import httpx
except ImportError as exc:  # pragma: no cover — exercised only without the extra installed
    raise ImportError(
        "ElevenLabsVoiceProvider requires the 'elevenlabs' package. "
        "Install it with: pip install 'velora[elevenlabs]'"
    ) from exc

__all__ = ["ElevenLabsVoiceProvider"]

# "Rachel" — a premade voice available on every ElevenLabs plan, so a
# freshly configured Provider works without first cloning or picking a
# voice from the account's library.
_DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
_DEFAULT_MODEL_ID = "eleven_multilingual_v2"
_AUDIO_FORMAT = "mp3"

_UNAUTHORIZED_STATUS_CODE = 401
_RATE_LIMITED_STATUS_CODE = 429


class ElevenLabsVoiceProvider:
    """:class:`~velora.providers.voice.VoiceProvider` backed by ElevenLabs.

    Implements :class:`~velora.runtime.LifecycleComponent`: :meth:`start`
    creates the underlying HTTP client (and its connection pool);
    :meth:`stop` closes it — same pattern
    ``AnthropicTextGenerationProvider`` already established. Builds and
    injects its own ``httpx.Client`` explicitly, rather than letting the
    SDK build one internally and reaching into a private attribute to
    close it (ADR-0013).
    """

    def __init__(
        self,
        *,
        api_key: str,
        voice_id: str = _DEFAULT_VOICE_ID,
        model_id: str = _DEFAULT_MODEL_ID,
    ) -> None:
        self._api_key = api_key
        self._voice_id = voice_id
        self._model_id = model_id
        self._http_client: httpx.Client | None = None
        self._client: elevenlabs.ElevenLabs | None = None

    @property
    def name(self) -> str:
        return "elevenlabs-voice"

    def start(self, context: RuntimeContext) -> None:
        del context
        self._http_client = httpx.Client()
        self._client = elevenlabs.ElevenLabs(api_key=self._api_key, httpx_client=self._http_client)

    def stop(self, context: RuntimeContext) -> None:
        del context
        if self._http_client is not None:
            self._http_client.close()
            self._http_client = None
        self._client = None

    def synthesize(self, request: SpeechRequest) -> SpeechResult:
        """
        :raises ProviderRequestError: called before :meth:`start`, or the
            backend rejects the request for a reason not covered below.
        :raises ProviderAuthenticationError: invalid or missing credentials.
        :raises ProviderRateLimitError: the backend rejected the request
            for rate limiting.
        :raises ProviderConnectionError: the backend could not be reached.
        """
        if self._client is None:
            raise ProviderRequestError(
                "ElevenLabsVoiceProvider.synthesize() called before start()."
            )

        try:
            chunks = self._client.text_to_speech.convert(
                self._voice_id, text=request.text, model_id=self._model_id
            )
            audio = b"".join(chunks)
        except elevenlabs.errors.UnprocessableEntityError as exc:
            raise ProviderRequestError(str(exc)) from exc
        except elevenlabs.core.ApiError as exc:
            # Unlike `anthropic`, this SDK has no dedicated exception
            # class per HTTP status beyond 422 (see ADR-0013): every
            # other non-2xx response — including 401 and 429 — arrives
            # as this same generic `ApiError`, distinguished only by
            # `status_code`.
            if exc.status_code == _UNAUTHORIZED_STATUS_CODE:
                raise ProviderAuthenticationError(str(exc)) from exc
            if exc.status_code == _RATE_LIMITED_STATUS_CODE:
                raise ProviderRateLimitError(str(exc)) from exc
            raise ProviderRequestError(str(exc)) from exc
        except httpx.HTTPError as exc:
            # Connection-level failures (DNS, timeout, refused
            # connection) aren't wrapped by the SDK at all — `httpx`
            # raises them directly (ADR-0013).
            raise ProviderConnectionError(str(exc)) from exc

        return SpeechResult(audio=audio, audio_format=_AUDIO_FORMAT)
