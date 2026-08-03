"""Error hierarchy shared by every Provider domain.

architecture.md original §9: "Los Providers nunca contienen lógica de
negocio" — they are pure adapters. Part of being a pure adapter is never
leaking a vendor SDK's own exception types to callers: a caller of
``TextGenerationProvider.generate()`` must be able to catch
``ProviderRateLimitError`` without knowing or caring whether the
concrete provider is Anthropic, OpenAI, or anything else. Every concrete
Provider across every domain (text, voice, image, video, music,
translation — see ``docs/VISION.md``) translates its vendor SDK's
exceptions into this shared hierarchy.
"""

from __future__ import annotations

__all__ = [
    "ProviderAuthenticationError",
    "ProviderConnectionError",
    "ProviderRateLimitError",
    "ProviderRequestError",
    "VeloraProviderError",
]


class VeloraProviderError(Exception):
    """Base class for all errors raised by any Provider, in any domain."""


class ProviderAuthenticationError(VeloraProviderError):
    """Raised when a Provider's credentials are missing, invalid, or expired."""


class ProviderRateLimitError(VeloraProviderError):
    """Raised when a Provider's backend rejects a request for rate limiting."""


class ProviderConnectionError(VeloraProviderError):
    """Raised when a Provider cannot reach its backend (network failure, timeout)."""


class ProviderRequestError(VeloraProviderError):
    """Raised when a Provider's backend rejects a request for any other reason.

    Covers malformed requests, content policy refusals, server-side
    errors, and any backend failure not covered by the more specific
    errors above.
    """
