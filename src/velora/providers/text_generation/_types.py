"""Typed shapes for the text-generation Provider domain.

Deliberately provider-agnostic: nothing here mentions Anthropic, OpenAI,
or any concrete vendor. ``system`` is a dedicated field, not a message
with a "system" role, because not every vendor's API models it as a
message (Anthropic's Messages API takes it as a separate top-level
parameter; modeling it as a field here, rather than folding it into
``messages``, keeps every concrete Provider's translation logic a
straightforward mapping instead of a per-vendor special case buried in
message-list handling).

Synchronous and non-streaming only, for now: the rest of the codebase
has no asynchronous execution model yet, and streaming is a real,
separate design surface (partial results, backpressure) that deserves
its own PR rather than being folded in here. Both are additive,
non-breaking extensions of :class:`TextGenerationProvider` when they
arrive.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["Message", "Role", "TextGenerationRequest", "TextGenerationResult"]


@unique
class Role(Enum):
    """Who a :class:`Message` in a conversation came from."""

    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True, slots=True)
class Message:
    """One turn in a conversation."""

    role: Role
    content: str


@dataclass(frozen=True, slots=True)
class TextGenerationRequest:
    """A provider-agnostic request to generate text.

    ``messages`` holds only user/assistant turns; ``system`` is separate
    (see module docstring).
    """

    messages: Sequence[Message]
    max_tokens: int
    system: str | None = None
    temperature: float | None = None


@dataclass(frozen=True, slots=True)
class TextGenerationResult:
    """A provider-agnostic result from a text-generation request."""

    text: str
    stop_reason: str
    input_tokens: int
    output_tokens: int
