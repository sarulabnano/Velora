"""Shared, typed parsing over a :class:`ConfigSource`.

This is Configuration's "single entry point" (architecture.md original
§6): raw strings go in, typed values or typed errors come out. New
settings classes reuse these functions instead of duplicating parsing
logic; new parsing functions are added here only when a real caller
needs them (not ahead of that need).
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from velora.configuration._errors import (
    InvalidConfigurationValueError,
    MissingConfigurationValueError,
)

if TYPE_CHECKING:
    from velora.configuration._sources import ConfigSource

__all__ = ["parse_enum"]


def parse_enum[E: Enum](
    source: ConfigSource,
    key: str,
    enum_type: type[E],
    *,
    default: E | None = None,
) -> E:
    """Resolve ``key`` from ``source`` as a member of ``enum_type``.

    The raw value is matched case-insensitively against member *names*
    (e.g. ``"production"`` or ``"PRODUCTION"`` both match
    ``Environment.PRODUCTION``).

    :raises MissingConfigurationValueError: ``key`` is absent from
        ``source`` and no ``default`` was given.
    :raises InvalidConfigurationValueError: ``key`` is present but does
        not match any member of ``enum_type``.
    """
    raw = source.get(key)

    if raw is None:
        if default is not None:
            return default
        raise MissingConfigurationValueError(f"Missing required configuration value: '{key}'.")

    normalized = raw.strip().upper()
    try:
        return enum_type[normalized]
    except KeyError as exc:
        valid_names = ", ".join(member.name for member in enum_type)
        raise InvalidConfigurationValueError(
            f"Invalid value '{raw}' for configuration key '{key}'. Expected one of: {valid_names}."
        ) from exc
