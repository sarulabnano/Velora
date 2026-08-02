"""Command-line entrypoint for Velora.

This entrypoint reports package metadata (`--version`, `--help`) and, by
default, is the composition root: it resolves Configuration, then
bootstraps the Runtime (ADR-0005). Per ADR-0002, this module is extended
across roadmap phases, never rewritten: `--version` and `--help` keep
working exactly as they did in the Foundation phase.
"""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

from velora import __version__
from velora.configuration import VeloraConfigurationError, VeloraSettings, load_settings
from velora.runtime import Runtime, VeloraRuntimeError

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

_PROG_NAME = "velora"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=_PROG_NAME,
        description="Velora — a composable, ten-year-stable AI platform runtime.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{_PROG_NAME} {__version__}",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    settings_loader: Callable[[], VeloraSettings] = load_settings,
    runtime_factory: Callable[[], Runtime] = Runtime,
) -> int:
    """Entry point invoked by the `velora` console script.

    Resolves Configuration, bootstraps a Runtime, reports its execution
    id and resolved environment, and shuts it down cleanly.
    `settings_loader` and `runtime_factory` exist so callers — tests, and
    later roadmap phases wiring real components — can inject
    preconfigured instances instead of the parameterless defaults; the
    CLI never constructs their internal dependencies itself.

    Configuration is resolved before the Runtime is constructed (ADR-0005):
    a configuration failure is reported the same way a runtime failure
    is, without ever having started anything that would need shutting
    down.

    Returns the process exit code. Argument parsing errors and `--help`/
    `--version` are handled by argparse, which exits the process directly;
    this function's return value covers the remaining paths.
    """
    parser = _build_parser()
    parser.parse_args(argv)

    try:
        settings = settings_loader()
    except VeloraConfigurationError as exc:
        print(f"{_PROG_NAME}: fatal: {exc}", file=sys.stderr)
        return 1

    runtime = runtime_factory()
    try:
        with runtime:
            print(
                f"{_PROG_NAME} {__version__} — runtime {runtime.context.runtime_id} "
                f"running ({settings.environment.value})."
            )
    except VeloraRuntimeError as exc:
        print(f"{_PROG_NAME}: fatal: {exc}", file=sys.stderr)
        return 1

    print(f"{_PROG_NAME} {__version__} — runtime stopped cleanly.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
