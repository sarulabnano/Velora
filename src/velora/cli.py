"""Command-line entrypoint for Velora.

This entrypoint reports package metadata (`--version`, `--help`) and, by
default, is the composition root: it resolves Configuration, configures
Logging, then bootstraps the Runtime with Logging attached as a
listener and Services' `SystemClock`/`UUIDIdGenerator` injected in place
of Runtime's own defaults (ADR-0005, ADR-0006, ADR-0007). Per ADR-0002,
this module is extended across roadmap phases, never rewritten:
`--version` and `--help`, and the default no-argument smoke-run, keep
working exactly as they did in earlier phases.

Since PR-009 (ADR-0012), this module also has its first real subcommand:
`velora create story`, running `velora.workflows.story.StoryWorkflow`
end to end. It builds its own, separate `Runtime` (with the Provider as
that Runtime's one `LifecycleComponent`) rather than reusing
`runtime_factory` — the one the default smoke-run already exposes for
injection — so that path, and every test written against its existing
single-argument contract, is untouched by this extension.
"""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING, Protocol

from velora import __version__
from velora.configuration import LogLevel as ConfigurationLogLevel
from velora.configuration import VeloraConfigurationError, VeloraSettings, load_settings
from velora.logging import LoggingSettings, RuntimeEventLogger, configure_logging
from velora.logging import LogLevel as LoggingLogLevel
from velora.providers import VeloraProviderError
from velora.runtime import Runtime, VeloraRuntimeError
from velora.services import SystemClock, UUIDIdGenerator

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from velora.engines.story import Story
    from velora.providers.text_generation import TextGenerationProvider
    from velora.runtime import LifecycleComponent, RuntimeEventListener

    class _StoryTextGenerationProvider(TextGenerationProvider, LifecycleComponent, Protocol):
        """What `create story` actually needs from its Provider: both
        `TextGenerationProvider` (what `NarrationService` needs) and
        `LifecycleComponent` (what `Runtime` needs) — `create story`
        registers the Provider as the Runtime's one component, so a
        Provider satisfying only the first, on its own, isn't enough."""


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

    # `dest="command"` is not `required`: no subcommand at all is a valid
    # invocation — it's the default smoke-run, unchanged since PR-002.
    subparsers = parser.add_subparsers(dest="command")

    create_parser = subparsers.add_parser(
        "create",
        help="Create content by running a Workflow (velora.workflows).",
    )
    # `required=True` here, unlike above: once "create" is chosen, a
    # target is not optional — there is no meaningful default deliverable.
    create_subparsers = create_parser.add_subparsers(dest="create_target", required=True)

    story_parser = create_subparsers.add_parser(
        "story",
        help=(
            "Generate a narrated, scene-divided Story from a topic "
            "(StoryWorkflow). Requires VELORA_ANTHROPIC_API_KEY."
        ),
    )
    story_parser.add_argument("--topic", required=True, help="The topic to narrate.")
    story_parser.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="Maximum tokens for the underlying generation call (default: 1024).",
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


def _default_text_generation_provider_factory(api_key: str) -> _StoryTextGenerationProvider:
    """Build the default TextGenerationProvider for `create story`.

    Imports `AnthropicTextGenerationProvider` lazily, inside this
    function body — not at module level — so that importing
    `velora.cli` (and running every command other than `create story`)
    never requires the optional `velora[anthropic]` extra (ADR-0009,
    ADR-0012). If it's missing, the `ImportError` `velora.providers.
    text_generation` already raises on import explains how to install it
    — no need to duplicate that message here.
    """
    from velora.providers.text_generation import AnthropicTextGenerationProvider

    return AnthropicTextGenerationProvider(api_key=api_key)


def _default_workflow_runtime_factory(
    listeners: Sequence[RuntimeEventListener],
    components: Sequence[LifecycleComponent],
) -> Runtime:
    """Build the Runtime that hosts `create story`'s Provider component.

    A separate factory from `_default_runtime_factory` (used by the
    default smoke-run) — not that one made more general — so the
    smoke-run's existing single-argument `runtime_factory` contract, and
    every test written against it, is untouched by this extension
    (ADR-0002, ADR-0012).
    """
    return Runtime(
        components=components,
        listeners=listeners,
        clock=SystemClock(),
        id_generator=UUIDIdGenerator(),
    )


def _run_create_story(
    args: argparse.Namespace,
    *,
    settings: VeloraSettings,
    event_logger: RuntimeEventLogger,
    provider_factory: Callable[[str], _StoryTextGenerationProvider],
    workflow_runtime_factory: Callable[
        [Sequence[RuntimeEventListener], Sequence[LifecycleComponent]], Runtime
    ],
) -> int:
    """Run `velora create story`: `StoryWorkflow`, end to end.

    Builds the full dependency chain itself — Provider, NarrationService,
    StoryEngine, StoryWorkflow — exactly as the composition root already
    does for Runtime/Logging: no intermediate layer constructs its own
    dependencies. `NarrationService`, `StoryEngine`, and `StoryWorkflow`
    are imported here, not at module level, for the same reason
    `_default_text_generation_provider_factory` defers its own import
    (ADR-0012): none of them are needed by any command other than this
    one.

    Requires `settings.anthropic_api_key` — checked before constructing
    anything, the same "fail fast before side effects" pattern `main`
    already uses for a `VeloraConfigurationError`.
    """
    if settings.anthropic_api_key is None:
        print(
            f"{_PROG_NAME}: fatal: VELORA_ANTHROPIC_API_KEY is required for 'create story'.",
            file=sys.stderr,
        )
        return 1

    from velora.engines.story import StoryEngine
    from velora.services.narration import NarrationService
    from velora.workflows.story import StoryWorkflow

    provider = provider_factory(settings.anthropic_api_key)
    workflow = StoryWorkflow(StoryEngine(NarrationService(provider)))

    runtime = workflow_runtime_factory([event_logger], [provider])
    try:
        with runtime:
            story: Story = workflow.run(args.topic, max_tokens=args.max_tokens)
    except (VeloraRuntimeError, VeloraProviderError, ValueError) as exc:
        print(f"{_PROG_NAME}: fatal: {exc}", file=sys.stderr)
        return 1

    print(f"Story: {story.topic} ({len(story.scenes)} scene(s))")
    for scene in story.scenes:
        print(f"\n[{scene.index}] {scene.text}")

    return 0


def main(
    argv: Sequence[str] | None = None,
    *,
    settings_loader: Callable[[], VeloraSettings] = load_settings,
    logging_factory: Callable[[LoggingSettings], RuntimeEventLogger] = configure_logging,
    runtime_factory: Callable[[Sequence[RuntimeEventListener]], Runtime] = _default_runtime_factory,
    provider_factory: Callable[
        [str], _StoryTextGenerationProvider
    ] = _default_text_generation_provider_factory,
    workflow_runtime_factory: Callable[
        [Sequence[RuntimeEventListener], Sequence[LifecycleComponent]], Runtime
    ] = _default_workflow_runtime_factory,
) -> int:
    """Entry point invoked by the `velora` console script.

    With no subcommand, resolves Configuration, configures Logging from
    it, bootstraps a Runtime with Logging attached as a listener,
    reports the Runtime's execution id and resolved environment, and
    shuts it down cleanly — unchanged since PR-002/PR-003/PR-004.
    `settings_loader`, `logging_factory`, and `runtime_factory` exist so
    callers — tests, and later roadmap phases wiring real components —
    can inject preconfigured instances instead of the parameterless
    defaults; the CLI never constructs their internal dependencies
    itself.

    With `create story` (PR-009, ADR-0012), runs `StoryWorkflow` end to
    end instead — see `_run_create_story`. `provider_factory` and
    `workflow_runtime_factory` exist for the same injection reason as
    the three parameters above, scoped to that path; `runtime_factory`
    itself is never reused for it, by design (ADR-0012).

    Configuration is resolved before Logging or any Runtime exist
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
    args = parser.parse_args(argv)

    try:
        settings = settings_loader()
    except VeloraConfigurationError as exc:
        print(f"{_PROG_NAME}: fatal: {exc}", file=sys.stderr)
        return 1

    logging_settings = LoggingSettings(level=_translate_log_level(settings.log_level))
    event_logger = logging_factory(logging_settings)

    if args.command == "create" and args.create_target == "story":
        return _run_create_story(
            args,
            settings=settings,
            event_logger=event_logger,
            provider_factory=provider_factory,
            workflow_runtime_factory=workflow_runtime_factory,
        )

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
