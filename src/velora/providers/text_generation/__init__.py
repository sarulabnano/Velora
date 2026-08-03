"""The text-generation Provider domain: generating text from a conversation.

The provider-agnostic contract (:class:`TextGenerationProvider`,
:class:`TextGenerationRequest`, :class:`TextGenerationResult`) and its
first concrete implementation, :class:`AnthropicTextGenerationProvider`.
Future PRs add more concrete Providers here (OpenAI, Gemini, Ollama,
LM Studio — see ``docs/VISION.md``) implementing the same
:class:`TextGenerationProvider` contract, without changing it.
"""

from __future__ import annotations

from velora.providers.text_generation._anthropic import AnthropicTextGenerationProvider
from velora.providers.text_generation._protocol import TextGenerationProvider
from velora.providers.text_generation._types import (
    Message,
    Role,
    TextGenerationRequest,
    TextGenerationResult,
)

__all__ = [
    "AnthropicTextGenerationProvider",
    "Message",
    "Role",
    "TextGenerationProvider",
    "TextGenerationRequest",
    "TextGenerationResult",
]
