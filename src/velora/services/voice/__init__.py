"""The voice capability Service.

Depends on ``velora.providers`` — unlike the infrastructure Services at
the root of ``velora.services`` (``Clock``, ``IdGenerator``), which do
not. Same "Services de capacidad" category as
``velora.services.narration`` (ADR-0010), kept in its own subpackage
rather than the package root, so importing ``velora.services`` (for
`Clock`/`IdGenerator`) never pulls in `velora.providers` for code that
doesn't need it.
"""

from __future__ import annotations

from velora.services.voice._service import VoiceService

__all__ = ["VoiceService"]
