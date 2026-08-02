"""The resolved, typed configuration of a Velora process."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from velora.configuration._environment import Environment
from velora.configuration._parsing import parse_enum

if TYPE_CHECKING:
    from velora.configuration._sources import ConfigSource

__all__ = ["VeloraSettings"]

_ENVIRONMENT_KEY = "VELORA_ENVIRONMENT"


@dataclass(frozen=True, slots=True)
class VeloraSettings:
    """Velora's resolved, typed configuration.

    Constructed only through :meth:`from_source` (or the package-level
    :func:`velora.configuration.load_settings` convenience function) —
    never by reading raw sources ad hoc elsewhere in the codebase.
    """

    environment: Environment

    @classmethod
    def from_source(cls, source: ConfigSource) -> VeloraSettings:
        """Resolve settings from ``source``.

        :raises InvalidConfigurationValueError: ``VELORA_ENVIRONMENT`` is
            set to a value that isn't a valid :class:`Environment` member.
        """
        environment = parse_enum(
            source,
            _ENVIRONMENT_KEY,
            Environment,
            default=Environment.DEVELOPMENT,
        )
        return cls(environment=environment)
