"""ImageService: the third capability Service (ADR-0018).

``docs/VISION.md``: Services "representan capacidades del sistema... no
representan APIs" -- the same principle ADR-0010 and ADR-0014 already
applied to ``NarrationService`` and ``VoiceService``, for the
``image`` domain instead. This wraps
:class:`~velora.providers.image.ImageProvider` -- the caller never
knows, or needs to know, which concrete Provider drew.

Deliberately thin: it does not decide what to draw beyond the prompt
it's given (model, size, and quality live on the injected Provider,
ADR-0017), nor accumulate configuration no real caller needs yet.
Deciding *when* to generate an image, and how it fits into a larger
pipeline, is business logic that belongs to a future Engine or
Workflow -- this Service only knows how to turn a prompt into an
image.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from velora.providers.image import ImageRequest

if TYPE_CHECKING:
    from velora.providers.image import ImageProvider, ImageResult

__all__ = ["ImageService"]


class ImageService:
    """Generates images via an injected
    :class:`~velora.providers.image.ImageProvider`.

    The Provider is a dependency, never constructed internally -- this
    Service does not know, and must not know, whether it is talking to
    OpenAI, Flux, Stable Diffusion, or anything else.
    """

    def __init__(self, provider: ImageProvider) -> None:
        self._provider = provider

    def draw(self, prompt: str) -> ImageResult:
        """Generate an image for ``prompt``.

        :raises ValueError: ``prompt`` is empty or only whitespace.
        :raises ~velora.providers.VeloraProviderError: the underlying
            Provider failed -- see its own error hierarchy for specifics
            (authentication, rate limiting, connection, or other).
        """
        if not prompt.strip():
            raise ValueError("prompt must not be empty.")

        return self._provider.generate(ImageRequest(prompt=prompt))
