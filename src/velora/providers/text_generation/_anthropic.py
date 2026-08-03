"""TextGenerationProvider backed by the Anthropic Messages API.

Contains no business logic — only translation between the generic
``TextGenerationRequest``/``TextGenerationResult`` contract and the
``anthropic`` SDK's own request/response shapes and exceptions.

Requires the ``anthropic`` package (the ``velora[anthropic]`` extra).
Importing this module without it installed raises ``ImportError`` with
that guidance, rather than a bare ``ModuleNotFoundError`` — no other
Provider needs it, so it is never a required dependency of
``velora`` itself.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from velora.providers._errors import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderRequestError,
)
from velora.providers.text_generation._types import TextGenerationResult

if TYPE_CHECKING:
    from velora.providers.text_generation._types import TextGenerationRequest
    from velora.runtime import RuntimeContext

try:
    import anthropic
except ImportError as exc:  # pragma: no cover — exercised only without the extra installed
    raise ImportError(
        "AnthropicTextGenerationProvider requires the 'anthropic' package. "
        "Install it with: pip install 'velora[anthropic]'"
    ) from exc

__all__ = ["AnthropicTextGenerationProvider"]

_DEFAULT_MODEL = "claude-sonnet-5"


class AnthropicTextGenerationProvider:
    """:class:`~velora.providers.text_generation.TextGenerationProvider`
    backed by Anthropic.

    Implements :class:`~velora.runtime.LifecycleComponent`: :meth:`start`
    creates the underlying SDK client (and its HTTP connection pool);
    :meth:`stop` closes it. Unlike Configuration, Logging, or the
    infrastructure Services (ADR-0005, ADR-0007), this Provider *does*
    hold a real resource — the first concrete, non-test implementer of
    ``LifecycleComponent`` in the codebase.
    """

    def __init__(self, *, api_key: str, model: str = _DEFAULT_MODEL) -> None:
        self._api_key = api_key
        self._model = model
        self._client: anthropic.Anthropic | None = None

    @property
    def name(self) -> str:
        return "anthropic-text-generation"

    def start(self, context: RuntimeContext) -> None:
        del context
        self._client = anthropic.Anthropic(api_key=self._api_key)

    def stop(self, context: RuntimeContext) -> None:
        del context
        if self._client is not None:
            self._client.close()
            self._client = None

    def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
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
                "AnthropicTextGenerationProvider.generate() called before start()."
            )

        kwargs: dict[str, object] = {
            "model": self._model,
            "max_tokens": request.max_tokens,
            "messages": [{"role": m.role.value, "content": m.content} for m in request.messages],
        }
        if request.system is not None:
            kwargs["system"] = request.system
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature

        try:
            response = self._client.messages.create(**kwargs)  # type: ignore[call-overload]
        except anthropic.AuthenticationError as exc:
            raise ProviderAuthenticationError(str(exc)) from exc
        except anthropic.RateLimitError as exc:
            raise ProviderRateLimitError(str(exc)) from exc
        except anthropic.APIConnectionError as exc:
            raise ProviderConnectionError(str(exc)) from exc
        except anthropic.APIStatusError as exc:
            raise ProviderRequestError(str(exc)) from exc

        text = "".join(block.text for block in response.content if block.type == "text")
        return TextGenerationResult(
            text=text,
            stop_reason=response.stop_reason or "unknown",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
