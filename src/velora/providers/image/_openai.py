"""ImageProvider backed by the OpenAI Images API (DALL-E).

Contains no business logic -- only translation between the generic
``ImageRequest``/``ImageResult`` contract and the ``openai`` SDK's own
request/response shapes and exceptions.

Requires the ``openai`` package (the ``velora[openai]`` extra).
Importing this module without it installed raises ``ImportError`` with
that guidance, rather than a bare ``ModuleNotFoundError`` -- same
pattern ``_anthropic.py`` and ``_elevenlabs.py`` already established:
no other Provider needs it, so it is never a required dependency of
``velora`` itself.
"""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING

from velora.providers._errors import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderRequestError,
)
from velora.providers.image._types import ImageResult

if TYPE_CHECKING:
    from velora.providers.image._types import ImageRequest
    from velora.runtime import RuntimeContext

try:
    import httpx
    import openai
except ImportError as exc:  # pragma: no cover — exercised only without the extra installed
    raise ImportError(
        "OpenAIImageProvider requires the 'openai' package. "
        "Install it with: pip install 'velora[openai]'"
    ) from exc

__all__ = ["OpenAIImageProvider"]

_DEFAULT_MODEL = "dall-e-3"
_DEFAULT_SIZE = "1024x1024"
_IMAGE_FORMAT = "png"


class OpenAIImageProvider:
    """:class:`~velora.providers.image.ImageProvider` backed by OpenAI.

    Implements :class:`~velora.runtime.LifecycleComponent`: :meth:`start`
    creates the underlying SDK client (and its HTTP connection pool);
    :meth:`stop` closes it -- same pattern
    ``AnthropicTextGenerationProvider`` and ``ElevenLabsVoiceProvider``
    already established. Builds and injects its own ``httpx.Client``
    explicitly, rather than letting the SDK build one internally and
    reaching into a private attribute to close it -- same reasoning
    ADR-0013 already applied to ``ElevenLabsVoiceProvider``: the SDK's
    ``OpenAI`` client accepts an ``http_client`` of its own, so nothing
    forces the alternative.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str = _DEFAULT_MODEL,
        size: str = _DEFAULT_SIZE,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._size = size
        self._http_client: httpx.Client | None = None
        self._client: openai.OpenAI | None = None

    @property
    def name(self) -> str:
        return "openai-image"

    def start(self, context: RuntimeContext) -> None:
        del context
        self._http_client = httpx.Client()
        self._client = openai.OpenAI(api_key=self._api_key, http_client=self._http_client)

    def stop(self, context: RuntimeContext) -> None:
        del context
        if self._http_client is not None:
            self._http_client.close()
            self._http_client = None
        self._client = None

    def generate(self, request: ImageRequest) -> ImageResult:
        """
        :raises ProviderRequestError: called before :meth:`start`, or the
            backend rejects the request for a reason not covered below.
        :raises ProviderAuthenticationError: invalid or missing credentials.
        :raises ProviderRateLimitError: the backend rejected the request
            for rate limiting.
        :raises ProviderConnectionError: the backend could not be reached.
        """
        if self._client is None:
            raise ProviderRequestError("OpenAIImageProvider.generate() called before start().")

        try:
            response = self._client.images.generate(
                model=self._model,
                prompt=request.prompt,
                size=self._size,
                n=1,
                response_format="b64_json",
            )
        except openai.AuthenticationError as exc:
            raise ProviderAuthenticationError(str(exc)) from exc
        except openai.RateLimitError as exc:
            raise ProviderRateLimitError(str(exc)) from exc
        except openai.APIConnectionError as exc:
            raise ProviderConnectionError(str(exc)) from exc
        except openai.APIStatusError as exc:
            raise ProviderRequestError(str(exc)) from exc

        if not response.data or response.data[0].b64_json is None:
            raise ProviderRequestError("OpenAI returned no image data.")

        image = base64.b64decode(response.data[0].b64_json)
        return ImageResult(image=image, image_format=_IMAGE_FORMAT)
