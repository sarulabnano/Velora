"""Tests for velora.providers.text_generation type shapes."""

from __future__ import annotations

import dataclasses

import pytest

from velora.providers.text_generation import Message, Role, TextGenerationRequest


def test_role_has_user_and_assistant_only() -> None:
    assert {member.name for member in Role} == {"USER", "ASSISTANT"}


def test_message_is_frozen() -> None:
    message = Message(role=Role.USER, content="hello")

    with pytest.raises(dataclasses.FrozenInstanceError):
        message.content = "changed"  # type: ignore[misc]


def test_request_defaults_system_and_temperature_to_none() -> None:
    request = TextGenerationRequest(
        messages=[Message(role=Role.USER, content="hi")],
        max_tokens=100,
    )

    assert request.system is None
    assert request.temperature is None


def test_request_is_frozen() -> None:
    request = TextGenerationRequest(messages=[], max_tokens=100)

    with pytest.raises(dataclasses.FrozenInstanceError):
        request.max_tokens = 200  # type: ignore[misc]
