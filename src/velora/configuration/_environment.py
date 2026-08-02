"""Deployment environment."""

from __future__ import annotations

from enum import Enum, unique

__all__ = ["Environment"]


@unique
class Environment(Enum):
    """The environment Velora is running in.

    This is the first, minimal setting Configuration resolves: nearly
    every application needs to know which environment it's in before
    anything else. Additional settings are added by future PRs as real
    consumers (Logging, Services, Providers) need them — not
    speculatively ahead of that need.
    """

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
