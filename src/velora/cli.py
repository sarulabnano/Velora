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

Since PR-013 (ADR-0016), `create story` runs the extended
`StoryWorkflow`: both `StoryEngine` and `NarrationAudioEngine`, so it
now also builds a `VoiceProvider` and registers it as a second
`LifecycleComponent` on that same dedicated Runtime, alongside the
`TextGenerationProvider`.

Since PR-016 (ADR-0019), `create story` runs the further extended
`StoryWorkflow`: `StoryEngine`, `NarrationAudioEngine`, and
`SceneImageEngine`, so it now also builds an `ImageProvider` and
registers it as a third `LifecycleComponent` on that same dedicated
Runtime.

Since PR-017 (ADR-0020), `create story` also persists its result to
disk: a `story.txt` transcript plus one audio and one image file per
scene, under `<output-dir>/<runtime-id>/` — `<output-dir>` defaults to
the current directory; `<runtime-id>` is the same id the Runtime itself
already generates per run, reused rather than inventing a second
identifier.

Since PR-018 (ADR-0021), `create story` runs the further extended
`StoryWorkflow`: `StoryEngine`, `NarrationAudioEngine`,
`SceneImageEngine`, and `SubtitleEngine`. Unlike the other three,
`SubtitleEngine` needs no Provider and requires no API key — it's
constructed directly, with no factory to inject and no
`LifecycleComponent` to register on the Runtime. `create story` also
now saves a `story.srt` file alongside the transcript.

Since PR-019 (ADR-0022), subtitle timing is measured from each scene's
real synthesized audio rather than estimated from word count alone;
`--words-per-minute` now only controls the fallback rate used when a
scene's duration can't be measured.

Since PR-020 (ADR-0023), `create story` also builds a `TimelineEngine`
(no Provider, no API key) and saves its result as `timeline.json` — a
manifest naming each scene's saved audio/image files alongside its
timing, so the output directory can be consumed programmatically
without re-deriving that alignment.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
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

    from velora.providers.image import ImageProvider
    from velora.providers.text_generation import TextGenerationProvider
    from velora.providers.voice import VoiceProvider
    from velora.runtime import LifecycleComponent, RuntimeEventListener
    from velora.workflows.story import NarratedStory

    class _StoryTextGenerationProvider(TextGenerationProvider, LifecycleComponent, Protocol):
        """What `create story` actually needs from its text Provider:
        both `TextGenerationProvider` (what `NarrationService` needs)
        and `LifecycleComponent` (what `Runtime` needs) — `create
        story` registers the Provider as one of the Runtime's
        components, so a Provider satisfying only the first, on its
        own, isn't enough."""

    class _StoryVoiceProvider(VoiceProvider, LifecycleComponent, Protocol):
        """What `create story` actually needs from its voice Provider,
        since PR-013 (ADR-0016): both `VoiceProvider` (what
        `VoiceService` needs) and `LifecycleComponent` (what `Runtime`
        needs) — same reasoning as `_StoryTextGenerationProvider`,
        for the second Provider this command now registers."""

    class _StoryImageProvider(ImageProvider, LifecycleComponent, Protocol):
        """What `create story` actually needs from its image Provider,
        since PR-016 (ADR-0019): both `ImageProvider` (what
        `ImageService` needs) and `LifecycleComponent` (what `Runtime`
        needs) — same reasoning as `_StoryTextGenerationProvider`,
        for the third Provider this command now registers."""


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
            "Generate a narrated, scene-divided, synthesized, "
            "illustrated Story from a topic (StoryWorkflow). Requires "
            "VELORA_ANTHROPIC_API_KEY, VELORA_ELEVENLABS_API_KEY, and "
            "VELORA_OPENAI_API_KEY."
        ),
    )
    story_parser.add_argument("--topic", required=True, help="The topic to narrate.")
    story_parser.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="Maximum tokens for the underlying generation call (default: 1024).",
    )
    story_parser.add_argument(
        "--output-dir",
        default=".",
        help=(
            "Directory under which to save the generated Story. A "
            "subdirectory named after the run's Runtime id is created "
            "inside it (default: current directory)."
        ),
    )
    story_parser.add_argument(
        "--words-per-minute",
        type=float,
        default=150.0,
        help=(
            "Fallback narration pace for timing subtitles, used only "
            "for a scene whose generated audio duration can't be "
            "measured (default: 150.0)."
        ),
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


def _default_voice_provider_factory(api_key: str) -> _StoryVoiceProvider:
    """Build the default VoiceProvider for `create story`.

    Imports `ElevenLabsVoiceProvider` lazily, inside this function body
    — not at module level — for the same reason
    `_default_text_generation_provider_factory` defers its own import
    (ADR-0012, ADR-0016): importing `velora.cli` (and running every
    command other than `create story`) must never require the optional
    `velora[elevenlabs]` extra. If it's missing, the `ImportError`
    `velora.providers.voice` already raises on import explains how to
    install it.
    """
    from velora.providers.voice import ElevenLabsVoiceProvider

    return ElevenLabsVoiceProvider(api_key=api_key)


def _default_image_provider_factory(api_key: str) -> _StoryImageProvider:
    """Build the default ImageProvider for `create story`.

    Imports `OpenAIImageProvider` lazily, inside this function body —
    not at module level — for the same reason
    `_default_text_generation_provider_factory` defers its own import
    (ADR-0012, ADR-0019): importing `velora.cli` (and running every
    command other than `create story`) must never require the optional
    `velora[openai]` extra. If it's missing, the `ImportError`
    `velora.providers.image` already raises on import explains how to
    install it.
    """
    from velora.providers.image import OpenAIImageProvider

    return OpenAIImageProvider(api_key=api_key)


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


def _save_narrated_story(narrated_story: NarratedStory, output_dir: Path) -> None:
    """Persist a `NarratedStory` to `output_dir` (ADR-0020, ADR-0021,
    ADR-0023).

    Writes one `scene_{index:03d}.{format}` file per scene for both
    `narrated_story.audio` and `narrated_story.images`, a `story.txt`
    transcript (the topic and every scene's text, the same content
    `_run_create_story` already prints to stdout), a single `story.srt`
    file (all scenes' captions, via `velora.engines.subtitle.render_srt`)
    — one shared file, not one per scene, since an SRT file's cues
    already carry their own scene boundaries; splitting it per scene
    would only make it harder to load into a video editor as a single
    subtitle track — and, since PR-020 (ADR-0023), a `timeline.json`
    manifest: one entry per scene, naming the audio and image files
    already written above and repeating that scene's timing from
    `narrated_story.timeline`, so a future Render step (or any external
    tool) can align everything without re-deriving which files or
    timestamps belong to which scene. `output_dir` alone is a complete,
    self-contained deliverable: audio, images, captions, a machine-
    readable manifest, and the text that ties them together, not just
    the binary artifacts.

    `output_dir` is created (with any missing parents) if it doesn't
    exist yet — mirrors `mkdir -p`, since a fresh, generated
    subdirectory (see `_run_create_story`) never exists beforehand.

    :raises OSError: `output_dir` could not be created, or a file could
        not be written to it (permissions, a full disk, and so on).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    story = narrated_story.story
    transcript_lines = [f"Story: {story.topic}", ""]
    for scene in story.scenes:
        transcript_lines.append(f"[{scene.index}] {scene.text}")
    (output_dir / "story.txt").write_text("\n".join(transcript_lines) + "\n", encoding="utf-8")

    from velora.engines.subtitle import render_srt

    (output_dir / "story.srt").write_text(render_srt(narrated_story.subtitles), encoding="utf-8")

    for scene_audio in narrated_story.audio.scenes:
        path = output_dir / f"scene_{scene_audio.index:03d}.{scene_audio.audio_format}"
        path.write_bytes(scene_audio.audio)

    for scene_image in narrated_story.images.scenes:
        path = output_dir / f"scene_{scene_image.index:03d}.{scene_image.image_format}"
        path.write_bytes(scene_image.image)

    timeline_manifest = {
        "topic": narrated_story.timeline.topic,
        "scenes": [
            {
                "index": scene.index,
                "text": scene.text,
                "audio_file": f"scene_{scene.index:03d}.{scene.audio_format}",
                "image_file": f"scene_{scene.index:03d}.{scene.image_format}",
                "start_seconds": scene.start_seconds,
                "end_seconds": scene.end_seconds,
            }
            for scene in narrated_story.timeline.scenes
        ],
    }
    (output_dir / "timeline.json").write_text(
        json.dumps(timeline_manifest, indent=2) + "\n", encoding="utf-8"
    )


def _run_create_story(
    args: argparse.Namespace,
    *,
    settings: VeloraSettings,
    event_logger: RuntimeEventLogger,
    provider_factory: Callable[[str], _StoryTextGenerationProvider],
    voice_provider_factory: Callable[[str], _StoryVoiceProvider],
    image_provider_factory: Callable[[str], _StoryImageProvider],
    workflow_runtime_factory: Callable[
        [Sequence[RuntimeEventListener], Sequence[LifecycleComponent]], Runtime
    ],
) -> int:
    """Run `velora create story`: `StoryWorkflow`, end to end.

    Builds the full dependency chain itself — all three Providers, all
    three Services, all three Engines, `StoryWorkflow` — exactly as the
    composition root already does for Runtime/Logging: no intermediate
    layer constructs its own dependencies. `NarrationService`,
    `VoiceService`, `ImageService`, `StoryEngine`,
    `NarrationAudioEngine`, `SceneImageEngine`, and `StoryWorkflow` are
    imported here, not at module level, for the same reason
    `_default_text_generation_provider_factory` defers its own import
    (ADR-0012): none of them are needed by any command other than this
    one.

    Requires `settings.anthropic_api_key`, `settings.elevenlabs_api_key`
    (ADR-0016), and `settings.openai_api_key` (ADR-0019) — checked
    before constructing anything, the same "fail fast before side
    effects" pattern `main` already uses for a
    `VeloraConfigurationError`.

    On success, persists the result via `_save_narrated_story` before
    printing anything (ADR-0020) — printing describes what was written,
    so writing must happen first; a failure writing to disk is reported
    the same "fatal" way as every other failure path here, distinct
    from `VeloraRuntimeError`/`VeloraProviderError`/`ValueError` only in
    that it's an `OSError`.
    """
    if settings.anthropic_api_key is None:
        print(
            f"{_PROG_NAME}: fatal: VELORA_ANTHROPIC_API_KEY is required for 'create story'.",
            file=sys.stderr,
        )
        return 1

    if settings.elevenlabs_api_key is None:
        print(
            f"{_PROG_NAME}: fatal: VELORA_ELEVENLABS_API_KEY is required for 'create story'.",
            file=sys.stderr,
        )
        return 1

    if settings.openai_api_key is None:
        print(
            f"{_PROG_NAME}: fatal: VELORA_OPENAI_API_KEY is required for 'create story'.",
            file=sys.stderr,
        )
        return 1

    from velora.engines.narration_audio import NarrationAudioEngine
    from velora.engines.scene_image import SceneImageEngine
    from velora.engines.story import StoryEngine
    from velora.engines.subtitle import SubtitleEngine
    from velora.engines.timeline import TimelineEngine
    from velora.services.image import ImageService
    from velora.services.narration import NarrationService
    from velora.services.voice import VoiceService
    from velora.workflows.story import StoryWorkflow

    text_provider = provider_factory(settings.anthropic_api_key)
    voice_provider = voice_provider_factory(settings.elevenlabs_api_key)
    image_provider = image_provider_factory(settings.openai_api_key)
    workflow = StoryWorkflow(
        StoryEngine(NarrationService(text_provider)),
        NarrationAudioEngine(VoiceService(voice_provider)),
        SceneImageEngine(ImageService(image_provider)),
        SubtitleEngine(words_per_minute=args.words_per_minute),
        TimelineEngine(),
    )

    runtime = workflow_runtime_factory(
        [event_logger], [text_provider, voice_provider, image_provider]
    )
    try:
        with runtime:
            narrated_story: NarratedStory = workflow.run(args.topic, max_tokens=args.max_tokens)
    except (VeloraRuntimeError, VeloraProviderError, ValueError) as exc:
        print(f"{_PROG_NAME}: fatal: {exc}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir) / runtime.context.runtime_id
    try:
        _save_narrated_story(narrated_story, output_dir)
    except OSError as exc:
        print(f"{_PROG_NAME}: fatal: {exc}", file=sys.stderr)
        return 1

    story = narrated_story.story
    print(f"Story: {story.topic} ({len(story.scenes)} scene(s))")
    print(f"Saved to: {output_dir}")
    print("Subtitles: story.srt")
    print("Timeline: timeline.json")
    for scene, scene_audio, scene_image in zip(
        story.scenes, narrated_story.audio.scenes, narrated_story.images.scenes, strict=True
    ):
        print(f"\n[{scene.index}] {scene.text}")
        print(f"    audio: scene_{scene.index:03d}.{scene_audio.audio_format}")
        print(f"    image: scene_{scene.index:03d}.{scene_image.image_format}")

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
    voice_provider_factory: Callable[[str], _StoryVoiceProvider] = _default_voice_provider_factory,
    image_provider_factory: Callable[[str], _StoryImageProvider] = _default_image_provider_factory,
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
    itself is never reused for it, by design (ADR-0012). Since PR-013
    (ADR-0016), that path also needs `voice_provider_factory`, injected
    for the same reason. Since PR-016 (ADR-0019), it also needs
    `image_provider_factory`, injected for the same reason.

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
            voice_provider_factory=voice_provider_factory,
            image_provider_factory=image_provider_factory,
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
