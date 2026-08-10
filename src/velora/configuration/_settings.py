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
_ANTHROPIC_API_KEY_KEY = "VELORA_ANTHROPIC_API_KEY"
_ELEVENLABS_API_KEY_KEY = "VELORA_ELEVENLABS_API_KEY"


@dataclass(frozen=True, slots=True)
class VeloraSettings:
    """Velora's resolved, typed configuration.

    Constructed only through :meth:`from_source` (or the package-level
    :func:`velora.configuration.load_settings` convenience function) —
    never by reading raw sources ad hoc elsewhere in the codebase.

    ``anthropic_api_key`` is the raw value of
    ``VELORA_ANTHROPIC_API_KEY``, or ``None`` if unset. Unlike
    ``environment``/``log_level``, presence is never required here: most
    of ``velora`` (the default smoke-run, ``--version``) doesn't need
    it. Whoever does — ``velora create story``, per ADR-0012 — checks
    for ``None`` itself, at the point of use, instead of this layer
    enforcing it for every caller.

    ``elevenlabs_api_key`` is the raw value of
    ``VELORA_ELEVENLABS_API_KEY``, or ``None`` if unset — same
    optional-until-point-of-use treatment as ``anthropic_api_key``, now
    that ``create story`` needs it too (ADR-0016).
    """

    environment: Environment
    log_level: LogLevel
    anthropic_api_key: str | None = None
    elevenlabs_api_key: str | None = None

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
        anthropic_api_key = source.get(_ANTHROPIC_API_KEY_KEY)
        elevenlabs_api_key = source.get(_ELEVENLABS_API_KEY_KEY)
        return cls(
            environment=environment,
            log_level=log_level,
            anthropic_api_key=anthropic_api_key,
            elevenlabs_api_key=elevenlabs_api_key,
        )
