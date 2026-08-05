"""Tests for the velora CLI entrypoint (the composition root)."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

import pytest

from velora import __version__
from velora.cli import main
from velora.configuration import Environment, VeloraConfigurationError, VeloraSettings
from velora.configuration import LogLevel as ConfigurationLogLevel
from velora.logging import LoggingSettings, RuntimeEventLogger
from velora.logging import LogLevel as LoggingLogLevel
from velora.providers import ProviderAuthenticationError
from velora.providers.text_generation import TextGenerationRequest, TextGenerationResult
from velora.runtime import Runtime, RuntimeContext, RuntimeEventListener, RuntimeState

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

_DEVELOPMENT_SETTINGS = VeloraSettings(
    environment=Environment.DEVELOPMENT,
    log_level=ConfigurationLogLevel.INFO,
)

_DEVELOPMENT_SETTINGS_WITH_API_KEY = VeloraSettings(
    environment=Environment.DEVELOPMENT,
    log_level=ConfigurationLogLevel.INFO,
    anthropic_api_key="sk-ant-test-value",
)


def _settings_loader() -> VeloraSettings:
    return _DEVELOPMENT_SETTINGS


def _settings_loader_with_api_key() -> VeloraSettings:
    return _DEVELOPMENT_SETTINGS_WITH_API_KEY


def test_main_returns_zero_on_success(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([], settings_loader=_settings_loader)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "velora" in captured.out
    assert __version__ in captured.out


def test_main_reports_runtime_execution_id(capsys: pytest.CaptureFixture[str]) -> None:
    main([], settings_loader=_settings_loader)

    captured = capsys.readouterr()
    assert "running" in captured.out
    assert "stopped cleanly" in captured.out


def test_main_reports_resolved_environment(capsys: pytest.CaptureFixture[str]) -> None:
    def _production_settings() -> VeloraSettings:
        return VeloraSettings(
            environment=Environment.PRODUCTION, log_level=ConfigurationLogLevel.INFO
        )

    main([], settings_loader=_production_settings)

    captured = capsys.readouterr()
    assert "production" in captured.out


def test_main_bootstraps_and_stops_the_injected_runtime() -> None:
    runtime = Runtime()

    exit_code = main(
        [],
        settings_loader=_settings_loader,
        runtime_factory=lambda listeners: runtime,
    )

    assert exit_code == 0
    assert runtime.state is RuntimeState.STOPPED


def test_default_runtime_factory_produces_a_real_runtime_id(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The default runtime_factory injects Services' Clock/IdGenerator
    (ADR-0007); this checks the observable result end to end, through
    the same real defaults `velora` uses on the command line."""
    main([], settings_loader=_settings_loader)

    captured = capsys.readouterr()
    assert "running (development)" in captured.out


def test_main_passes_configured_logger_to_runtime_factory() -> None:
    received: list[Sequence[RuntimeEventListener]] = []

    def _runtime_factory(listeners: Sequence[RuntimeEventListener]) -> Runtime:
        received.append(listeners)
        return Runtime(listeners=listeners)

    main([], settings_loader=_settings_loader, runtime_factory=_runtime_factory)

    assert len(received) == 1
    assert len(received[0]) == 1
    assert isinstance(received[0][0], RuntimeEventListener)


def test_main_translates_resolved_log_level_into_logging_settings() -> None:
    captured_settings: list[LoggingSettings] = []

    def _logging_factory(settings: LoggingSettings) -> RuntimeEventLogger:
        captured_settings.append(settings)
        return RuntimeEventLogger(settings, stream=io.StringIO())

    def _debug_settings() -> VeloraSettings:
        return VeloraSettings(
            environment=Environment.DEVELOPMENT, log_level=ConfigurationLogLevel.DEBUG
        )

    main([], settings_loader=_debug_settings, logging_factory=_logging_factory)

    assert len(captured_settings) == 1
    assert captured_settings[0].level is LoggingLogLevel.DEBUG


def test_main_logs_lifecycle_events_via_real_logging_backend(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main([], settings_loader=_settings_loader)

    captured = capsys.readouterr()
    assert "runtime bootstrap starting" in captured.err
    assert "runtime bootstrap completed" in captured.err
    assert "runtime shutdown completed" in captured.err


def test_main_reports_configuration_error_and_exits_nonzero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def _failing_settings_loader() -> VeloraSettings:
        raise VeloraConfigurationError("VELORA_ENVIRONMENT is invalid")

    exit_code = main([], settings_loader=_failing_settings_loader)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "fatal" in captured.err
    assert "VELORA_ENVIRONMENT" in captured.err


def test_configuration_error_never_configures_logging_or_constructs_a_runtime() -> None:
    def _failing_settings_loader() -> VeloraSettings:
        raise VeloraConfigurationError("bad config")

    def _logging_factory(settings: LoggingSettings) -> RuntimeEventLogger:
        pytest.fail("Logging must not be configured when Configuration fails")

    def _runtime_factory(listeners: Sequence[RuntimeEventListener]) -> Runtime:
        pytest.fail("Runtime must not be constructed when Configuration fails")

    main(
        [],
        settings_loader=_failing_settings_loader,
        logging_factory=_logging_factory,
        runtime_factory=_runtime_factory,
    )


def test_main_reports_fatal_runtime_error_and_exits_nonzero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _FailingComponent:
        @property
        def name(self) -> str:
            return "unstable"

        def start(self, context: RuntimeContext) -> None:
            del context
            raise ValueError("cannot start")

        def stop(self, context: RuntimeContext) -> None:
            del context

    def _runtime_factory(listeners: Sequence[RuntimeEventListener]) -> Runtime:
        return Runtime(components=[_FailingComponent()], listeners=listeners)

    exit_code = main([], settings_loader=_settings_loader, runtime_factory=_runtime_factory)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "fatal" in captured.err
    # The real Logging backend also recorded the failure independently.
    assert "fatal error in component 'unstable'" in captured.err


def test_version_flag_exits_zero_and_prints_version(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert __version__ in captured.out


def test_unknown_argument_exits_nonzero() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--not-a-real-flag"])

    assert exc_info.value.code != 0


class _FakeTextGenerationProvider:
    """Satisfies both LifecycleComponent and TextGenerationProvider —
    `create story` registers the Provider as the Runtime's one
    component, so a fake standing in for it must satisfy both."""

    def __init__(self, text: str = "First scene.\n\nSecond scene.") -> None:
        self._text = text
        self.received_requests: list[TextGenerationRequest] = []
        self.started = False
        self.stopped = False

    @property
    def name(self) -> str:
        return "fake-text-generation"

    def start(self, context: RuntimeContext) -> None:
        del context
        self.started = True

    def stop(self, context: RuntimeContext) -> None:
        del context
        self.stopped = True

    def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
        self.received_requests.append(request)
        return TextGenerationResult(
            text=self._text, stop_reason="end_turn", input_tokens=10, output_tokens=20
        )


def _provider_factory(
    provider: _FakeTextGenerationProvider,
) -> tuple[Callable[[str], _FakeTextGenerationProvider], list[str]]:
    received_api_keys: list[str] = []

    def _factory(api_key: str) -> _FakeTextGenerationProvider:
        received_api_keys.append(api_key)
        return provider

    return _factory, received_api_keys


def test_create_story_returns_zero_and_prints_the_scenes(
    capsys: pytest.CaptureFixture[str],
) -> None:
    provider = _FakeTextGenerationProvider("The city wakes.\n\nNight falls.")
    factory, _ = _provider_factory(provider)

    exit_code = main(
        ["create", "story", "--topic", "A day in the city"],
        settings_loader=_settings_loader_with_api_key,
        provider_factory=factory,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Story: A day in the city (2 scene(s))" in captured.out
    assert "[0] The city wakes." in captured.out
    assert "[1] Night falls." in captured.out


def test_create_story_starts_and_stops_the_provider_via_runtime() -> None:
    provider = _FakeTextGenerationProvider()
    factory, _ = _provider_factory(provider)

    main(
        ["create", "story", "--topic", "Anything"],
        settings_loader=_settings_loader_with_api_key,
        provider_factory=factory,
    )

    assert provider.started
    assert provider.stopped


def test_create_story_passes_the_configured_api_key_to_provider_factory() -> None:
    provider = _FakeTextGenerationProvider()
    factory, received_api_keys = _provider_factory(provider)

    main(
        ["create", "story", "--topic", "Anything"],
        settings_loader=_settings_loader_with_api_key,
        provider_factory=factory,
    )

    assert received_api_keys == ["sk-ant-test-value"]


def test_create_story_passes_max_tokens_through_to_the_provider() -> None:
    provider = _FakeTextGenerationProvider()
    factory, _ = _provider_factory(provider)

    main(
        ["create", "story", "--topic", "Anything", "--max-tokens", "77"],
        settings_loader=_settings_loader_with_api_key,
        provider_factory=factory,
    )

    assert provider.received_requests[0].max_tokens == 77


def test_create_story_max_tokens_defaults_to_1024() -> None:
    provider = _FakeTextGenerationProvider()
    factory, _ = _provider_factory(provider)

    main(
        ["create", "story", "--topic", "Anything"],
        settings_loader=_settings_loader_with_api_key,
        provider_factory=factory,
    )

    assert provider.received_requests[0].max_tokens == 1024


def test_create_story_requires_api_key_and_never_constructs_a_provider(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def _failing_provider_factory(api_key: str) -> _FakeTextGenerationProvider:
        pytest.fail("Provider must not be constructed without a configured API key")

    exit_code = main(
        ["create", "story", "--topic", "Anything"],
        settings_loader=_settings_loader,  # anthropic_api_key defaults to None
        provider_factory=_failing_provider_factory,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "fatal" in captured.err
    assert "VELORA_ANTHROPIC_API_KEY" in captured.err


def test_create_story_reports_provider_error_and_exits_nonzero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _FailingProvider(_FakeTextGenerationProvider):
        def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
            del request
            raise ProviderAuthenticationError("invalid API key")

    factory, _ = _provider_factory(_FailingProvider())

    exit_code = main(
        ["create", "story", "--topic", "Anything"],
        settings_loader=_settings_loader_with_api_key,
        provider_factory=factory,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "fatal" in captured.err
    assert "invalid API key" in captured.err


def test_create_story_reports_runtime_bootstrap_error_and_exits_nonzero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _FailingStartProvider(_FakeTextGenerationProvider):
        def start(self, context: RuntimeContext) -> None:
            del context
            raise ValueError("cannot start provider")

    factory, _ = _provider_factory(_FailingStartProvider())

    exit_code = main(
        ["create", "story", "--topic", "Anything"],
        settings_loader=_settings_loader_with_api_key,
        provider_factory=factory,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "fatal" in captured.err


def test_create_story_rejects_empty_topic(capsys: pytest.CaptureFixture[str]) -> None:
    provider = _FakeTextGenerationProvider()
    factory, _ = _provider_factory(provider)

    exit_code = main(
        ["create", "story", "--topic", ""],
        settings_loader=_settings_loader_with_api_key,
        provider_factory=factory,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "fatal" in captured.err
    assert "must not be empty" in captured.err
    # The Runtime still starts and stops the Provider cleanly — the
    # precondition fails inside the Workflow, after bootstrap succeeds.
    assert provider.started
    assert provider.stopped


def test_create_requires_a_target() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["create"])

    assert exc_info.value.code != 0


def test_create_story_requires_topic() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["create", "story"])

    assert exc_info.value.code != 0


def test_default_provider_factory_builds_a_real_anthropic_provider(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exercises `_default_text_generation_provider_factory`'s deferred
    import (ADR-0012) end to end through `main`, without a real network
    call: substitutes a fake in place of `AnthropicTextGenerationProvider`
    at the import site the factory resolves lazily — the same boundary
    the real class would occupy."""
    provider = _FakeTextGenerationProvider("Only scene.")

    def _fake_anthropic_provider(*, api_key: str) -> _FakeTextGenerationProvider:
        del api_key
        return provider

    monkeypatch.setattr(
        "velora.providers.text_generation.AnthropicTextGenerationProvider",
        _fake_anthropic_provider,
    )

    exit_code = main(
        ["create", "story", "--topic", "Anything"],
        settings_loader=_settings_loader_with_api_key,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Only scene." in captured.out
