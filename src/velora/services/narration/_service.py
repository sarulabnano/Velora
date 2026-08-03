"""NarrationService: the first capability Service (ADR-0008).

``docs/VISION.md``: "Narration Service... puede usar GPT, Claude,
Gemini... sin cambiar el resto del proyecto." This wraps
:class:`~velora.providers.text_generation.TextGenerationProvider` — the
caller never knows, or needs to know, which concrete Provider answered.

Deliberately thin: it does not decide narration structure, tone, or
length beyond a generic system prompt. Deciding *what* to narrate, and
how a script is broken into scenes, is business logic that belongs to a
future Engine (VISION.md: "Story Engine construye la historia") — this
Service only knows how to turn instructions into narration text.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from velora.providers.text_generation import Message, Role, TextGenerationRequest

if TYPE_CHECKING:
    from velora.providers.text_generation import TextGenerationProvider, TextGenerationResult

__all__ = ["NarrationService"]

_DEFAULT_SYSTEM_PROMPT = (
    "You are a professional narration writer. Write clear, engaging "
    "narration text based on the given instructions. Respond only with "
    "the narration text itself — no preamble, no explanation, no "
    "formatting markers."
)


class NarrationService:
    """Generates narration text via an injected
    :class:`~velora.providers.text_generation.TextGenerationProvider`.

    The Provider is a dependency, never constructed internally — this
    Service does not know, and must not know, whether it is talking to
    Anthropic, OpenAI, or a local model.
    """

    def __init__(
        self,
        provider: TextGenerationProvider,
        *,
        system_prompt: str = _DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self._provider = provider
        self._system_prompt = system_prompt

    def narrate(self, instructions: str, *, max_tokens: int = 1024) -> TextGenerationResult:
        """Generate narration text for ``instructions``.

        :raises ValueError: ``instructions`` is empty or only whitespace.
        :raises ~velora.providers.VeloraProviderError: the underlying
            Provider failed — see its own error hierarchy for specifics
            (authentication, rate limiting, connection, or other).
        """
        if not instructions.strip():
            raise ValueError("instructions must not be empty.")

        request = TextGenerationRequest(
            messages=[Message(role=Role.USER, content=instructions)],
            max_tokens=max_tokens,
            system=self._system_prompt,
        )
        return self._provider.generate(request)
