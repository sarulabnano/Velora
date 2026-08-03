"""Velora Providers: pure adapters to external AI/media APIs.

architecture.md original §9 (and ``docs/VISION.md``): a Provider adapts
one external, concrete service (Anthropic, OpenAI, ElevenLabs, Flux,
Runway, Suno, DeepL, ...) to a typed, domain-specific contract. Every
Provider in the same domain implements the same contract; the rest of
the system never knows which concrete Provider it's talking to — only
the contract (ADR-0008: this is what a future capability Service, like
``NarrationService``, will depend on instead of any concrete Provider).

Providers never contain business logic. This root package holds only
the error hierarchy shared across every domain. Each domain — this PR
introduces ``text_generation`` — is its own subpackage with its own
typed request/result shapes and its own Protocol, because a text
generation call and an image generation call have nothing in common
beyond "call an external AI service."
"""

from __future__ import annotations

from velora.providers._errors import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderRequestError,
    VeloraProviderError,
)

__all__ = [
    "ProviderAuthenticationError",
    "ProviderConnectionError",
    "ProviderRateLimitError",
    "ProviderRequestError",
    "VeloraProviderError",
]
