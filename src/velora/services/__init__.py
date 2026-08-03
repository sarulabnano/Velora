"""Velora Services: infrastructure and capability, provider-agnostic.

ADR-0008 distinguishes two categories, both legitimately "Services"
(``docs/VISION.md``: "representan capacidades del sistema, no
representan APIs"), with different positions in the dependency layering:

- **Infrastructure Services** — this package's root (`Clock`,
  `IdGenerator`). No dependency on `velora.providers`. Not every Service
  implements :class:`~velora.runtime.LifecycleComponent`: it does only
  when it holds a real resource to open and close. Neither `Clock` nor
  `IdGenerator` do (ADR-0007).
- **Capability Services** — their own subpackages (`narration`, ...).
  Depend on `velora.providers` for the concrete work; deliberately kept
  out of this root module so importing `Clock`/`IdGenerator` never pulls
  in a Provider dependency for code that doesn't need one.
"""

from __future__ import annotations

from velora.services._clock import Clock, SystemClock
from velora.services._id_generator import IdGenerator, UUIDIdGenerator

__all__ = ["Clock", "IdGenerator", "SystemClock", "UUIDIdGenerator"]
