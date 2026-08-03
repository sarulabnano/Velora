"""Tests for velora.runtime.UUIDIdGenerator."""

from __future__ import annotations

from uuid import UUID

from velora.runtime import IdGenerator, UUIDIdGenerator


def test_returns_a_valid_uuid4_string() -> None:
    result = UUIDIdGenerator().new_id()

    parsed = UUID(result, version=4)
    assert str(parsed) == result


def test_two_calls_return_different_ids() -> None:
    generator = UUIDIdGenerator()

    assert generator.new_id() != generator.new_id()


def test_is_recognized_as_an_id_generator() -> None:
    assert isinstance(UUIDIdGenerator(), IdGenerator)


def test_services_uuid_id_generator_satisfies_runtimes_id_generator_protocol() -> None:
    """Structural typing (ADR-0007): no import between the two packages."""
    from velora.services import UUIDIdGenerator as ServicesUUIDIdGenerator

    assert isinstance(ServicesUUIDIdGenerator(), IdGenerator)
