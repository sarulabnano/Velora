"""Typed shapes for the image Provider domain.

Deliberately provider-agnostic: nothing here mentions OpenAI, Flux,
Stable Diffusion, or any concrete vendor -- same discipline
``text_generation/_types.py`` and ``voice/_types.py`` already
established for their own domains (ADR-0009, ADR-0013).

Synchronous and non-streaming only, for now, for the same reason both
of those domains are: no consumer with an asynchronous execution model
or a real streaming need exists yet. Both are additive, non-breaking
extensions of :class:`~velora.providers.image.ImageProvider` when they
arrive.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["ImageRequest", "ImageResult"]


@dataclass(frozen=True, slots=True)
class ImageRequest:
    """A provider-agnostic request to generate an image from a prompt.

    Deliberately minimal: ``prompt`` is the only field that varies for
    the domain's single real caller today -- same reasoning
    ``SpeechRequest`` already applied to ``text`` (ADR-0013). Model,
    size, and quality live on the Provider itself (constructor
    parameters on
    :class:`~velora.providers.image.OpenAIImageProvider`), the same
    role ``model`` plays for
    :class:`~velora.providers.text_generation.AnthropicTextGenerationProvider`
    -- not here, because no real caller needs to vary them between
    successive calls to the same Provider yet. When one does, that is
    the moment to move the relevant parameter onto this type (Regla de
    oro).
    """

    prompt: str


@dataclass(frozen=True, slots=True)
class ImageResult:
    """A provider-agnostic result from an image-generation request.

    ``image_format`` is a plain string, not an enum: with exactly one
    real Provider producing exactly one format (``"png"``), a
    one-member enum would model a distinction that doesn't exist yet --
    same reasoning ``SpeechResult.audio_format`` already applied
    (ADR-0013).
    """

    image: bytes
    image_format: str
