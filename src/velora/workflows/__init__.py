"""Velora Workflows: orchestrating Engines into a complete, invokable pipeline.

``docs/VISION.md``: "Los Workflows conectan todos los motores." Each
Workflow is its own subpackage — the same shape as `velora.engines` and
`velora.providers`. This root holds nothing yet: no second Workflow has
revealed a genuine cross-workflow need (a shared contract, a shared
error hierarchy) to justify one. `velora.engines` and `velora.providers`
grew shared roots because more than one domain needed the same thing;
this package follows the same rule (Regla de oro, already applied by
ADR-0008 and ADR-0011): shared infrastructure appears when a second
Workflow actually needs it, not before.
"""

from __future__ import annotations
