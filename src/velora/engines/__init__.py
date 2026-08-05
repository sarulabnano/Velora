"""Velora Engines: complex, multi-step logic (architecture.md original §10).

Each Engine is its own subpackage. This root holds nothing yet — no
Engine has revealed a genuine cross-domain need (a shared error
hierarchy, a shared contract) to justify one. `velora.providers` and
`velora.services` grew shared roots because more than one domain needed
the same thing; this package follows the same rule: shared
infrastructure appears when a second Engine actually needs it, not
before (Regla de oro).
"""

from __future__ import annotations
