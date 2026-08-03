"""The narration capability Service.

Depends on ``velora.providers`` — unlike the infrastructure Services at
the root of ``velora.services`` (``Clock``, ``IdGenerator``), which do
not. This is the "Services de capacidad" category from ADR-0008, kept in
its own subpackage rather than the package root, so importing
``velora.services`` (for `Clock`/`IdGenerator`) never pulls in
`velora.providers` for code that doesn't need it.
"""

from __future__ import annotations

from velora.services.narration._service import NarrationService

__all__ = ["NarrationService"]
