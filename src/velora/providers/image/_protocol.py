"""The contract every image Provider implements."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from velora.providers.image._types import ImageRequest, ImageResult

__all__ = ["ImageProvider"]


@runtime_checkable
class ImageProvider(Protocol):
    """Generates an image from a prompt. The only contract callers know.

    "El sistema nunca conoce el proveedor. Solo conoce el contrato"
    (``docs/VISION.md``) -- mirrors
    :class:`~velora.providers.text_generation.TextGenerationProvider`
    and :class:`~velora.providers.voice.VoiceProvider` exactly, for the
    ``image`` domain instead (ADR-0009: each Provider domain is its own
    subpackage with its own contract, never a single generic
    ``Provider``).

    :raises ~velora.providers.ProviderAuthenticationError: invalid or
        missing credentials.
    :raises ~velora.providers.ProviderRateLimitError: the backend
        rejected the request for rate limiting.
    :raises ~velora.providers.ProviderConnectionError: the backend could
        not be reached.
    :raises ~velora.providers.ProviderRequestError: any other backend
        failure.
    """

    def generate(self, request: ImageRequest) -> ImageResult:
        """Generate an image for ``request``."""
        ...  # pragma: no cover — structural signature, never executed
