"""The image Provider domain: generating images from a text prompt.

The provider-agnostic contract (:class:`ImageProvider`,
:class:`ImageRequest`, :class:`ImageResult`) and its first concrete
implementation, :class:`OpenAIImageProvider`. Future PRs add more
concrete Providers here (Flux, Stable Diffusion, MidJourney -- see
``docs/VISION.md``) implementing the same :class:`ImageProvider`
contract, without changing it.
"""

from __future__ import annotations

from velora.providers.image._openai import OpenAIImageProvider
from velora.providers.image._protocol import ImageProvider
from velora.providers.image._types import ImageRequest, ImageResult

__all__ = [
    "ImageProvider",
    "ImageRequest",
    "ImageResult",
    "OpenAIImageProvider",
]
