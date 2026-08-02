"""Tests for the velora CLI entrypoint."""

from __future__ import annotations

import pytest

from velora import __version__
from velora.cli import main
from velora.runtime import Runtime, RuntimeContext


def test_main_returns_zero_on_success(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "velora" in captured.out
    assert __version__ in captured.out


def test_main_reports_runtime_execution_id(capsys: pytest.CaptureFixture[str]) -> None:
    main([])

    captured = capsys.readouterr()
    assert "running" in captured.out
    assert "stopped cleanly" in captured.out


def test_main_bootstraps_and_stops_the_injected_runtime() -> None:
    runtime = Runtime()

    exit_code = main([], runtime_factory=lambda: runtime)

    from velora.runtime import RuntimeState

    assert exit_code == 0
    assert runtime.state is RuntimeState.STOPPED


def test_main_reports_fatal_error_and_exits_nonzero(
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

    exit_code = main([], runtime_factory=lambda: Runtime(components=[_FailingComponent()]))

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "fatal" in captured.err


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
