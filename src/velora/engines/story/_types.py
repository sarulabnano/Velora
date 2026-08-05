"""Typed shapes produced by the Story Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["Scene", "Story"]


@dataclass(frozen=True, slots=True)
class Scene:
    """One ordered segment of a :class:`Story`."""

    index: int
    text: str


@dataclass(frozen=True, slots=True)
class Story:
    """A topic, narrated and divided into ordered scenes.

    ``scenes`` may be empty — a story with no content is a valid,
    unusual state to represent, not an error to raise (a future Timeline
    Engine can decide what to do with it).
    """

    topic: str
    scenes: Sequence[Scene]
