"""Configuration error hierarchy.

Per ADR-0001, Configuration never imports Logging and never writes logs.
Every failure is one of these typed exceptions, propagated to whoever
called the loader (the composition root — see ADR-0005), which decides
how to report it.
"""

from __future__ import annotations

__all__ = [
    "InvalidConfigurationValueError",
    "MissingConfigurationValueError",
    "VeloraConfigurationError",
]


class VeloraConfigurationError(Exception):
    """Base class for all errors raised by :mod:`velora.configuration`."""


class MissingConfigurationValueError(VeloraConfigurationError):
    """Raised when a required configuration value has no source and no default."""


class InvalidConfigurationValueError(VeloraConfigurationError):
    """Raised when a configuration value is present but fails to parse."""
