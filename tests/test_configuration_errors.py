"""Tests for velora.configuration error hierarchy."""

from __future__ import annotations

import pytest

from velora.configuration import (
    InvalidConfigurationValueError,
    MissingConfigurationValueError,
    VeloraConfigurationError,
)


@pytest.mark.parametrize(
    "error_type",
    [MissingConfigurationValueError, InvalidConfigurationValueError],
)
def test_every_configuration_error_derives_from_base(
    error_type: type[VeloraConfigurationError],
) -> None:
    assert issubclass(error_type, VeloraConfigurationError)
