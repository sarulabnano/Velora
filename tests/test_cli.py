"""Tests for the velora CLI entrypoint."""

from __future__ import annotations

import pytest

from velora import __version__
from velora.cli import main


def test_main_returns_zero_on_success(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "velora" in captured.out
    assert __version__ in captured.out


def test_main_reports_foundation_phase(capsys: pytest.CaptureFixture[str]) -> None:
    main([])

    captured = capsys.readouterr()
    assert "Foundation phase" in captured.out


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
