"""Velora Configuration: the single, typed entry point for settings.

Nothing outside this package reads ``os.environ`` (enforced by
``tests/test_no_direct_environ_access.py``). This module never imports
``velora.runtime`` or ``velora.logging`` — see ADR-0001 and ADR-0005 for
why, and for how the composition root connects the two.
"""

from __future__ import annotations

from velora.configuration._environment import Environment
from velora.configuration._errors import (
    InvalidConfigurationValueError,
    MissingConfigurationValueError,
    VeloraConfigurationError,
)
from velora.configuration._settings import VeloraSettings
from velora.configuration._sources import ConfigSource, EnvironmentSource

__all__ = [
    "ConfigSource",
    "Environment",
    "EnvironmentSource",
    "InvalidConfigurationValueError",
    "MissingConfigurationValueError",
    "VeloraConfigurationError",
    "VeloraSettings",
    "load_settings",
]


def load_settings(source: ConfigSource | None = None) -> VeloraSettings:
    """Resolve :class:`VeloraSettings` from ``source``.

    ``source`` defaults to :class:`EnvironmentSource` — process
    environment variables — which is what every real invocation of the
    ``velora`` CLI uses. Tests, and any future caller that needs a
    different origin, inject their own :class:`ConfigSource` instead.
    """
    return VeloraSettings.from_source(source if source is not None else EnvironmentSource())
