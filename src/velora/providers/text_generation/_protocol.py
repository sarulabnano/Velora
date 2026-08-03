"""The contract every text-generation Provider implements."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from velora.providers.text_generation._types import (
        TextGenerationRequest,
        TextGenerationResult,
    )

__all__ = ["TextGenerationProvider"]


@runtime_checkable
class TextGenerationProvider(Protocol):
    """Generates text from a conversation. The only contract callers know.

    "El sistema nunca conoce el proveedor. Solo conoce el contrato"
    (``docs/VISION.md``) — a future ``NarrationService`` depends on this
    Protocol, never on a concrete Provider class.

    :raises ~velora.providers.ProviderAuthenticationError: invalid or
        missing credentials.
    :raises ~velora.providers.ProviderRateLimitError: the backend
        rejected the request for rate limiting.
    :raises ~velora.providers.ProviderConnectionError: the backend could
        not be reached.
    :raises ~velora.providers.ProviderRequestError: any other backend
        failure.
    """

    def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
        """Generate text for ``request``."""
        ...  # pragma: no cover — structural signature, never executed
