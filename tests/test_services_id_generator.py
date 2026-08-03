"""Tests for velora.services.UUIDIdGenerator."""

from __future__ import annotations

from uuid import UUID

from velora.services import IdGenerator, UUIDIdGenerator


def test_returns_a_valid_uuid4_string() -> None:
    result = UUIDIdGenerator().new_id()

    parsed = UUID(result, version=4)
    assert str(parsed) == result


def test_two_calls_return_different_ids() -> None:
    generator = UUIDIdGenerator()

    assert generator.new_id() != generator.new_id()


def test_is_recognized_as_an_id_generator() -> None:
    assert isinstance(UUIDIdGenerator(), IdGenerator)


def test_object_without_new_id_is_not_an_id_generator() -> None:
    assert not isinstance(object(), IdGenerator)
