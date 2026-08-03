"""Command-line entrypoint for Velora.

This entrypoint reports package metadata (`--version`, `--help`) and, by
default, is the composition root: it resolves Configuration, configures
Logging, then bootstraps the Runtime with Logging attached as a
listener and Services' `SystemClock`/`UUIDIdGenerator` injected in place
of Runtime's own defaults (ADR-0005, ADR-0006, ADR-0007). Per ADR-0002,
this module is extended across roadmap phases, never rewritten:
`--version` and `--help` keep working exactly as they did in the
Foundation phase.
"""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

from velora import __version__
from velora.configuration import LogLevel as ConfigurationLogLevel
from velora.configuration import VeloraConfigurationError, VeloraSettings, load_settings
from velora.logging import LoggingSettings, RuntimeEventLogger, configure_logging
from velora.logging import LogLevel as LoggingLogLevel
from velora.runtime import Runtime, VeloraRuntimeError
from velora.services import SystemClock, UUIDIdGenerator

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from velora.runtime import RuntimeEventListener

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


def _translate_log_level(level: ConfigurationLogLevel) -> LoggingLogLevel:
    """Translate Configuration's LogLevel into Logging's LogLevel.

    The two are deliberately independent types (ADR-0006): neither
    package imports the other. The composition root is the only place
    that knows about both and bridges them, by name.
    """
    return LoggingLogLevel[level.name]


def _default_runtime_factory(listeners: Sequence[RuntimeEventListener]) -> Runtime:
    """Build the default Runtime, with Services' Clock/IdGenerator injected.

    ``velora.services.SystemClock``/``UUIDIdGenerator`` satisfy
    ``velora.runtime.Clock``/``IdGenerator`` structurally — neither
    package imports the other (ADR-0007). Passing them here, rather than
    relying on Runtime's own internal defaults, is the composition root
    making that substitutability real rather than theoretical.
    """
    return Runtime(listeners=listeners, clock=SystemClock(), id_generator=UUIDIdGenerator())


def main(
    argv: Sequence[str] | None = None,
    *,
    settings_loader: Callable[[], VeloraSettings] = load_settings,
    logging_factory: Callable[[LoggingSettings], RuntimeEventLogger] = configure_logging,
    runtime_factory: Callable[[Sequence[RuntimeEventListener]], Runtime] = _default_runtime_factory,
) -> int:
    """Entry point invoked by the `velora` console script.

    Resolves Configuration, configures Logging from it, bootstraps a
    Runtime with Logging attached as a listener, reports the Runtime's
    execution id and resolved environment, and shuts it down cleanly.
    `settings_loader`, `logging_factory`, and `runtime_factory` exist so
    callers — tests, and later roadmap phases wiring real components —
    can inject preconfigured instances instead of the parameterless
    defaults; the CLI never constructs their internal dependencies
    itself.

    Configuration is resolved before Logging or the Runtime exist
    (ADR-0005): a configuration failure is reported to stderr directly,
    the same way a runtime failure is, without ever having started
    anything that would need shutting down. Once Logging exists, it logs
    every Runtime lifecycle event (including a failing one) on its own;
    this function's own stderr message on a Runtime failure is not
    redundant with that — it is guaranteed to appear regardless of the
    configured log level, while the log line is not.

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

    logging_settings = LoggingSettings(level=_translate_log_level(settings.log_level))
    event_logger = logging_factory(logging_settings)

    runtime = runtime_factory([event_logger])
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
