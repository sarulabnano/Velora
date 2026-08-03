"""Velora Services: small, provider-agnostic, reusable capabilities.

Services sit between Configuration/Logging and Providers in the
dependency layering (architecture.md original §4:
``Providers → Services → Configuration → Logging → Runtime``). They may
depend on any layer below them; nothing below them may depend on this
package.

Not every Service implements
:class:`~velora.runtime.LifecycleComponent`: it does only when it holds
a real resource to open and close. Neither :class:`Clock` nor
:class:`IdGenerator` do — see ADR-0007.
"""

from __future__ import annotations

from velora.services._clock import Clock, SystemClock
from velora.services._id_generator import IdGenerator, UUIDIdGenerator

__all__ = ["Clock", "IdGenerator", "SystemClock", "UUIDIdGenerator"]
