"""Command-line entrypoint for Velora.

During the Foundation phase, this entrypoint reports package metadata.
Starting in the Runtime phase (PR-002), it will bootstrap and hand off
control to the Runtime. It is not a placeholder: `velora --version` and
`velora --help` are legitimate, permanent CLI behaviors that this module
will continue to own once the Runtime exists.
"""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

from velora import __version__

if TYPE_CHECKING:
    from collections.abc import Sequence

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


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point invoked by the `velora` console script.

    Returns the process exit code. Argument parsing errors and `--help`/
    `--version` are handled by argparse, which exits the process directly;
    this function's return value covers the remaining, successful paths.
    """
    parser = _build_parser()
    parser.parse_args(argv)
    print(f"{_PROG_NAME} {__version__} — Foundation phase. Runtime not yet initialized.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
