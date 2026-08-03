"""Tests for velora.providers error hierarchy."""

from __future__ import annotations

import pytest

from velora.providers import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderRateLimitError,
    ProviderRequestError,
    VeloraProviderError,
)


@pytest.mark.parametrize(
    "error_type",
    [
        ProviderAuthenticationError,
        ProviderConnectionError,
        ProviderRateLimitError,
        ProviderRequestError,
    ],
)
def test_every_provider_error_derives_from_base(
    error_type: type[VeloraProviderError],
) -> None:
    assert issubclass(error_type, VeloraProviderError)
