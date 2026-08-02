"""The resolved, typed configuration of a Velora process."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from velora.configuration._environment import Environment
from velora.configuration._log_level import LogLevel
from velora.configuration._parsing import parse_enum

if TYPE_CHECKING:
    from velora.configuration._sources import ConfigSource

__all__ = ["VeloraSettings"]

_ENVIRONMENT_KEY = "VELORA_ENVIRONMENT"
_LOG_LEVEL_KEY = "VELORA_LOG_LEVEL"


@dataclass(frozen=True, slots=True)
class VeloraSettings:
    """Velora's resolved, typed configuration.

    Constructed only through :meth:`from_source` (or the package-level
    :func:`velora.configuration.load_settings` convenience function) —
    never by reading raw sources ad hoc elsewhere in the codebase.
    """

    environment: Environment
    log_level: LogLevel

    @classmethod
    def from_source(cls, source: ConfigSource) -> VeloraSettings:
        """Resolve settings from ``source``.

        :raises InvalidConfigurationValueError: a value is set but isn't
            a valid member of its expected enum.
        """
        environment = parse_enum(
            source,
            _ENVIRONMENT_KEY,
            Environment,
            default=Environment.DEVELOPMENT,
        )
        log_level = parse_enum(
            source,
            _LOG_LEVEL_KEY,
            LogLevel,
            default=LogLevel.INFO,
        )
        return cls(environment=environment, log_level=log_level)
