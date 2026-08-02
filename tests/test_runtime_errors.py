"""Tests for velora.runtime error hierarchy."""

from __future__ import annotations

import pytest

from velora.runtime import (
    RuntimeAlreadyStartedError,
    RuntimeBootstrapError,
    RuntimeNotRunningError,
    RuntimeShutdownError,
    VeloraRuntimeError,
)


@pytest.mark.parametrize(
    "error_type",
    [
        RuntimeAlreadyStartedError,
        RuntimeNotRunningError,
        RuntimeBootstrapError,
        RuntimeShutdownError,
    ],
)
def test_every_runtime_error_derives_from_velora_runtime_error(
    error_type: type[VeloraRuntimeError],
) -> None:
    assert issubclass(error_type, VeloraRuntimeError)


def test_velora_runtime_error_does_not_shadow_builtin_runtime_error() -> None:
    assert not issubclass(VeloraRuntimeError, RuntimeError)
