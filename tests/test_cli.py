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
from velora.runtime import Runtime, RuntimeContext, RuntimeEventListener, RuntimeState

if TYPE_CHECKING:
    from collections.abc import Sequence

_DEVELOPMENT_SETTINGS = VeloraSettings(
    environment=Environment.DEVELOPMENT,
    log_level=ConfigurationLogLevel.INFO,
)


def _settings_loader() -> VeloraSettings:
    return _DEVELOPMENT_SETTINGS


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
