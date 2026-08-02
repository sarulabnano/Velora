"""Tests for velora.runtime.RuntimeContext."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from velora.runtime import RuntimeContext


def test_context_holds_given_fields() -> None:
    started_at = datetime.now(UTC)

    context = RuntimeContext(runtime_id="abc-123", started_at=started_at)

    assert context.runtime_id == "abc-123"
    assert context.started_at is started_at


def test_context_is_frozen() -> None:
    context = RuntimeContext(runtime_id="abc-123", started_at=datetime.now(UTC))

    with pytest.raises(dataclasses.FrozenInstanceError):
        context.runtime_id = "changed"  # type: ignore[misc]
