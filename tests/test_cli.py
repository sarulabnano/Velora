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
from velora.providers.image import ImageRequest, ImageResult
from velora.providers.text_generation import TextGenerationRequest, TextGenerationResult
from velora.providers.voice import SpeechRequest, SpeechResult
from velora.runtime import Runtime, RuntimeContext, RuntimeEventListener, RuntimeState

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

_DEVELOPMENT_SETTINGS = VeloraSettings(
    environment=Environment.DEVELOPMENT,
    log_level=ConfigurationLogLevel.INFO,
)

_DEVELOPMENT_SETTINGS_WITH_API_KEY = VeloraSettings(
    environment=Environment.DEVELOPMENT,
    log_level=ConfigurationLogLevel.INFO,
    anthropic_api_key="sk-ant-test-value",
)

_DEVELOPMENT_SETTINGS_WITH_ELEVENLABS_KEY_ONLY = VeloraSettings(
    environment=Environment.DEVELOPMENT,
    log_level=ConfigurationLogLevel.INFO,
    elevenlabs_api_key="el-test-value",
)

_DEVELOPMENT_SETTINGS_WITH_ANTHROPIC_AND_ELEVENLABS_KEYS = VeloraSettings(
    environment=Environment.DEVELOPMENT,
    log_level=ConfigurationLogLevel.INFO,
    anthropic_api_key="sk-ant-test-value",
    elevenlabs_api_key="el-test-value",
)

_DEVELOPMENT_SETTINGS_WITH_ALL_API_KEYS = VeloraSettings(
    environment=Environment.DEVELOPMENT,
    log_level=ConfigurationLogLevel.INFO,
    anthropic_api_key="sk-ant-test-value",
    elevenlabs_api_key="el-test-value",
    openai_api_key="oa-test-value",
)


def _settings_loader() -> VeloraSettings:
    return _DEVELOPMENT_SETTINGS


def _settings_loader_with_api_key() -> VeloraSettings:
    return _DEVELOPMENT_SETTINGS_WITH_API_KEY


def _settings_loader_with_elevenlabs_key_only() -> VeloraSettings:
    return _DEVELOPMENT_SETTINGS_WITH_ELEVENLABS_KEY_ONLY


def _settings_loader_with_anthropic_and_elevenlabs_keys() -> VeloraSettings:
    return _DEVELOPMENT_SETTINGS_WITH_ANTHROPIC_AND_ELEVENLABS_KEYS


def _settings_loader_with_all_api_keys() -> VeloraSettings:
    return _DEVELOPMENT_SETTINGS_WITH_ALL_API_KEYS


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
    """Satisfies both LifecycleComponent and TextGenerationProvider --
    `create story` registers the Provider as one of the Runtime's
    components, so a fake standing in for it must satisfy both."""

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


class _FakeVoiceProvider:
    """Satisfies both LifecycleComponent and VoiceProvider -- since
    PR-013 (ADR-0016), `create story` registers this Provider too, as
    the Runtime's second component."""

    def __init__(self) -> None:
        self.received_requests: list[SpeechRequest] = []
        self.started = False
        self.stopped = False

    @property
    def name(self) -> str:
        return "fake-voice"

    def start(self, context: RuntimeContext) -> None:
        del context
        self.started = True

    def stop(self, context: RuntimeContext) -> None:
        del context
        self.stopped = True

    def synthesize(self, request: SpeechRequest) -> SpeechResult:
        self.received_requests.append(request)
        return SpeechResult(audio=request.text.encode(), audio_format="mp3")


class _FakeImageProvider:
    """Satisfies both LifecycleComponent and ImageProvider -- since
    PR-016 (ADR-0019), `create story` registers this Provider too, as
    the Runtime's third component."""

    def __init__(self) -> None:
        self.received_requests: list[ImageRequest] = []
        self.started = False
        self.stopped = False

    @property
    def name(self) -> str:
        return "fake-image"

    def start(self, context: RuntimeContext) -> None:
        del context
        self.started = True

    def stop(self, context: RuntimeContext) -> None:
        del context
        self.stopped = True

    def generate(self, request: ImageRequest) -> ImageResult:
        self.received_requests.append(request)
        return ImageResult(image=request.prompt.encode(), image_format="png")


def _provider_factory(
    provider: _FakeTextGenerationProvider,
) -> tuple[Callable[[str], _FakeTextGenerationProvider], list[str]]:
    received_api_keys: list[str] = []

    def _factory(api_key: str) -> _FakeTextGenerationProvider:
        received_api_keys.append(api_key)
        return provider

    return _factory, received_api_keys


def _voice_provider_factory(
    provider: _FakeVoiceProvider,
) -> tuple[Callable[[str], _FakeVoiceProvider], list[str]]:
    received_api_keys: list[str] = []

    def _factory(api_key: str) -> _FakeVoiceProvider:
        received_api_keys.append(api_key)
        return provider

    return _factory, received_api_keys


def _image_provider_factory(
    provider: _FakeImageProvider,
) -> tuple[Callable[[str], _FakeImageProvider], list[str]]:
    received_api_keys: list[str] = []

    def _factory(api_key: str) -> _FakeImageProvider:
        received_api_keys.append(api_key)
        return provider

    return _factory, received_api_keys


def test_create_story_returns_zero_and_prints_the_scenes(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    provider = _FakeTextGenerationProvider("The city wakes.\n\nNight falls.")
    factory, _ = _provider_factory(provider)
    voice_factory, _ = _voice_provider_factory(_FakeVoiceProvider())
    image_factory, _ = _image_provider_factory(_FakeImageProvider())

    exit_code = main(
        ["create", "story", "--topic", "A day in the city", "--output-dir", str(tmp_path)],
        settings_loader=_settings_loader_with_all_api_keys,
        provider_factory=factory,
        voice_provider_factory=voice_factory,
        image_provider_factory=image_factory,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Story: A day in the city (2 scene(s))" in captured.out
    assert "[0] The city wakes." in captured.out
    assert "[1] Night falls." in captured.out


def test_create_story_saves_a_transcript_and_one_file_per_scene(tmp_path: Path) -> None:
    provider = _FakeTextGenerationProvider("The city wakes.\n\nNight falls.")
    factory, _ = _provider_factory(provider)
    voice_factory, _ = _voice_provider_factory(_FakeVoiceProvider())
    image_factory, _ = _image_provider_factory(_FakeImageProvider())

    exit_code = main(
        ["create", "story", "--topic", "A day in the city", "--output-dir", str(tmp_path)],
        settings_loader=_settings_loader_with_all_api_keys,
        provider_factory=factory,
        voice_provider_factory=voice_factory,
        image_provider_factory=image_factory,
    )
    assert exit_code == 0

    run_dirs = list(tmp_path.iterdir())
    assert len(run_dirs) == 1
    output_dir = run_dirs[0]

    transcript = (output_dir / "story.txt").read_text(encoding="utf-8")
    assert "Story: A day in the city" in transcript
    assert "[0] The city wakes." in transcript
    assert "[1] Night falls." in transcript

    assert (output_dir / "scene_000.mp3").read_bytes() == b"The city wakes."
    assert (output_dir / "scene_001.mp3").read_bytes() == b"Night falls."
    assert (output_dir / "scene_000.png").read_bytes() == b"The city wakes."
    assert (output_dir / "scene_001.png").read_bytes() == b"Night falls."

    srt = (output_dir / "story.srt").read_text(encoding="utf-8")
    assert "1\n" in srt
    assert "The city wakes." in srt
    assert "Night falls." in srt
    assert "-->" in srt


def test_create_story_prints_the_subtitles_filename(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    provider = _FakeTextGenerationProvider("A scene.")
    factory, _ = _provider_factory(provider)
    voice_factory, _ = _voice_provider_factory(_FakeVoiceProvider())
    image_factory, _ = _image_provider_factory(_FakeImageProvider())

    exit_code = main(
        ["create", "story", "--topic", "Anything", "--output-dir", str(tmp_path)],
        settings_loader=_settings_loader_with_all_api_keys,
        provider_factory=factory,
        voice_provider_factory=voice_factory,
        image_provider_factory=image_factory,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Subtitles: story.srt" in captured.out


def test_create_story_words_per_minute_affects_subtitle_timing(tmp_path: Path) -> None:
    provider = _FakeTextGenerationProvider(" ".join(["word"] * 60))
    factory, _ = _provider_factory(provider)
    voice_factory, _ = _voice_provider_factory(_FakeVoiceProvider())
    image_factory, _ = _image_provider_factory(_FakeImageProvider())

    exit_code = main(
        [
            "create",
            "story",
            "--topic",
            "Anything",
            "--output-dir",
            str(tmp_path),
            "--words-per-minute",
            "60",
        ],
        settings_loader=_settings_loader_with_all_api_keys,
        provider_factory=factory,
        voice_provider_factory=voice_factory,
        image_provider_factory=image_factory,
    )
    assert exit_code == 0

    output_dir = next(tmp_path.iterdir())
    srt = (output_dir / "story.srt").read_text(encoding="utf-8")
    # 60 words at 60 words/minute (1 word/second) should take about a minute.
    assert "00:01:00,000" in srt


def test_create_story_words_per_minute_defaults_to_150() -> None:
    from velora.cli import _build_parser

    parser = _build_parser()
    args = parser.parse_args(["create", "story", "--topic", "Anything"])

    assert args.words_per_minute == 150.0


def test_create_story_prints_the_output_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    provider = _FakeTextGenerationProvider("A scene.")
    factory, _ = _provider_factory(provider)
    voice_factory, _ = _voice_provider_factory(_FakeVoiceProvider())
    image_factory, _ = _image_provider_factory(_FakeImageProvider())

    exit_code = main(
        ["create", "story", "--topic", "Anything", "--output-dir", str(tmp_path)],
        settings_loader=_settings_loader_with_all_api_keys,
        provider_factory=factory,
        voice_provider_factory=voice_factory,
        image_provider_factory=image_factory,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    run_dirs = list(tmp_path.iterdir())
    assert len(run_dirs) == 1
    assert f"Saved to: {run_dirs[0]}" in captured.out


def test_create_story_output_dir_defaults_to_current_directory() -> None:
    from velora.cli import _build_parser

    parser = _build_parser()
    args = parser.parse_args(["create", "story", "--topic", "Anything"])

    assert args.output_dir == "."


def test_create_story_two_runs_get_separate_output_directories(tmp_path: Path) -> None:
    provider = _FakeTextGenerationProvider("A scene.")
    factory, _ = _provider_factory(provider)
    voice_factory, _ = _voice_provider_factory(_FakeVoiceProvider())
    image_factory, _ = _image_provider_factory(_FakeImageProvider())

    for _ in range(2):
        exit_code = main(
            ["create", "story", "--topic", "Anything", "--output-dir", str(tmp_path)],
            settings_loader=_settings_loader_with_all_api_keys,
            provider_factory=factory,
            voice_provider_factory=voice_factory,
            image_provider_factory=image_factory,
        )
        assert exit_code == 0

    assert len(list(tmp_path.iterdir())) == 2


def test_create_story_reports_disk_write_failure_and_exits_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # A file where the CLI needs to create a directory: os.makedirs
    # fails with FileExistsError (an OSError subclass).
    blocking_file = tmp_path / "blocked"
    blocking_file.write_text("not a directory")

    provider = _FakeTextGenerationProvider("A scene.")
    factory, _ = _provider_factory(provider)
    voice_factory, _ = _voice_provider_factory(_FakeVoiceProvider())
    image_factory, _ = _image_provider_factory(_FakeImageProvider())

    exit_code = main(
        ["create", "story", "--topic", "Anything", "--output-dir", str(blocking_file)],
        settings_loader=_settings_loader_with_all_api_keys,
        provider_factory=factory,
        voice_provider_factory=voice_factory,
        image_provider_factory=image_factory,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "fatal" in captured.err


def test_create_story_prints_audio_and_image_filenames_per_scene(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    provider = _FakeTextGenerationProvider("The city wakes.\n\nNight falls.")
    factory, _ = _provider_factory(provider)
    voice_factory, _ = _voice_provider_factory(_FakeVoiceProvider())
    image_factory, _ = _image_provider_factory(_FakeImageProvider())

    exit_code = main(
        ["create", "story", "--topic", "A day in the city", "--output-dir", str(tmp_path)],
        settings_loader=_settings_loader_with_all_api_keys,
        provider_factory=factory,
        voice_provider_factory=voice_factory,
        image_provider_factory=image_factory,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "audio: scene_000.mp3" in captured.out
    assert "audio: scene_001.mp3" in captured.out
    assert "image: scene_000.png" in captured.out
    assert "image: scene_001.png" in captured.out


def test_create_story_starts_and_stops_all_three_providers_via_runtime(tmp_path: Path) -> None:
    provider = _FakeTextGenerationProvider()
    factory, _ = _provider_factory(provider)
    voice_provider = _FakeVoiceProvider()
    voice_factory, _ = _voice_provider_factory(voice_provider)
    image_provider = _FakeImageProvider()
    image_factory, _ = _image_provider_factory(image_provider)

    main(
        ["create", "story", "--topic", "Anything", "--output-dir", str(tmp_path)],
        settings_loader=_settings_loader_with_all_api_keys,
        provider_factory=factory,
        voice_provider_factory=voice_factory,
        image_provider_factory=image_factory,
    )

    assert provider.started
    assert provider.stopped
    assert voice_provider.started
    assert voice_provider.stopped
    assert image_provider.started
    assert image_provider.stopped


def test_create_story_passes_the_configured_api_keys_to_the_provider_factories(
    tmp_path: Path,
) -> None:
    provider = _FakeTextGenerationProvider()
    factory, received_text_api_keys = _provider_factory(provider)
    voice_factory, received_voice_api_keys = _voice_provider_factory(_FakeVoiceProvider())
    image_factory, received_image_api_keys = _image_provider_factory(_FakeImageProvider())

    main(
        ["create", "story", "--topic", "Anything", "--output-dir", str(tmp_path)],
        settings_loader=_settings_loader_with_all_api_keys,
        provider_factory=factory,
        voice_provider_factory=voice_factory,
        image_provider_factory=image_factory,
    )

    assert received_text_api_keys == ["sk-ant-test-value"]
    assert received_voice_api_keys == ["el-test-value"]
    assert received_image_api_keys == ["oa-test-value"]


def test_create_story_passes_max_tokens_through_to_the_provider(tmp_path: Path) -> None:
    provider = _FakeTextGenerationProvider()
    factory, _ = _provider_factory(provider)
    voice_factory, _ = _voice_provider_factory(_FakeVoiceProvider())
    image_factory, _ = _image_provider_factory(_FakeImageProvider())

    main(
        [
            "create",
            "story",
            "--topic",
            "Anything",
            "--max-tokens",
            "77",
            "--output-dir",
            str(tmp_path),
        ],
        settings_loader=_settings_loader_with_all_api_keys,
        provider_factory=factory,
        voice_provider_factory=voice_factory,
        image_provider_factory=image_factory,
    )

    assert provider.received_requests[0].max_tokens == 77


def test_create_story_max_tokens_defaults_to_1024(tmp_path: Path) -> None:
    provider = _FakeTextGenerationProvider()
    factory, _ = _provider_factory(provider)
    voice_factory, _ = _voice_provider_factory(_FakeVoiceProvider())
    image_factory, _ = _image_provider_factory(_FakeImageProvider())

    main(
        ["create", "story", "--topic", "Anything", "--output-dir", str(tmp_path)],
        settings_loader=_settings_loader_with_all_api_keys,
        provider_factory=factory,
        voice_provider_factory=voice_factory,
        image_provider_factory=image_factory,
    )

    assert provider.received_requests[0].max_tokens == 1024


def test_create_story_requires_anthropic_api_key_and_never_constructs_a_provider(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def _failing_provider_factory(api_key: str) -> _FakeTextGenerationProvider:
        pytest.fail("Provider must not be constructed without a configured API key")

    def _failing_voice_provider_factory(api_key: str) -> _FakeVoiceProvider:
        pytest.fail("Provider must not be constructed without a configured API key")

    def _failing_image_provider_factory(api_key: str) -> _FakeImageProvider:
        pytest.fail("Provider must not be constructed without a configured API key")

    exit_code = main(
        ["create", "story", "--topic", "Anything"],
        settings_loader=_settings_loader_with_elevenlabs_key_only,  # no anthropic key
        provider_factory=_failing_provider_factory,
        voice_provider_factory=_failing_voice_provider_factory,
        image_provider_factory=_failing_image_provider_factory,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "fatal" in captured.err
    assert "VELORA_ANTHROPIC_API_KEY" in captured.err


def test_create_story_requires_elevenlabs_api_key_and_never_constructs_a_provider(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def _failing_provider_factory(api_key: str) -> _FakeTextGenerationProvider:
        pytest.fail("Provider must not be constructed without a configured API key")

    def _failing_voice_provider_factory(api_key: str) -> _FakeVoiceProvider:
        pytest.fail("Provider must not be constructed without a configured API key")

    def _failing_image_provider_factory(api_key: str) -> _FakeImageProvider:
        pytest.fail("Provider must not be constructed without a configured API key")

    exit_code = main(
        ["create", "story", "--topic", "Anything"],
        settings_loader=_settings_loader_with_api_key,  # anthropic only, no elevenlabs/openai
        provider_factory=_failing_provider_factory,
        voice_provider_factory=_failing_voice_provider_factory,
        image_provider_factory=_failing_image_provider_factory,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "fatal" in captured.err
    assert "VELORA_ELEVENLABS_API_KEY" in captured.err


def test_create_story_requires_openai_api_key_and_never_constructs_a_provider(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def _failing_provider_factory(api_key: str) -> _FakeTextGenerationProvider:
        pytest.fail("Provider must not be constructed without a configured API key")

    def _failing_voice_provider_factory(api_key: str) -> _FakeVoiceProvider:
        pytest.fail("Provider must not be constructed without a configured API key")

    def _failing_image_provider_factory(api_key: str) -> _FakeImageProvider:
        pytest.fail("Provider must not be constructed without a configured API key")

    exit_code = main(
        ["create", "story", "--topic", "Anything"],
        # anthropic + elevenlabs, no openai
        settings_loader=_settings_loader_with_anthropic_and_elevenlabs_keys,
        provider_factory=_failing_provider_factory,
        voice_provider_factory=_failing_voice_provider_factory,
        image_provider_factory=_failing_image_provider_factory,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "fatal" in captured.err
    assert "VELORA_OPENAI_API_KEY" in captured.err


def test_create_story_reports_provider_error_and_exits_nonzero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _FailingProvider(_FakeTextGenerationProvider):
        def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
            del request
            raise ProviderAuthenticationError("invalid API key")

    factory, _ = _provider_factory(_FailingProvider())
    voice_factory, _ = _voice_provider_factory(_FakeVoiceProvider())
    image_factory, _ = _image_provider_factory(_FakeImageProvider())

    exit_code = main(
        ["create", "story", "--topic", "Anything"],
        settings_loader=_settings_loader_with_all_api_keys,
        provider_factory=factory,
        voice_provider_factory=voice_factory,
        image_provider_factory=image_factory,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "fatal" in captured.err
    assert "invalid API key" in captured.err


def test_create_story_reports_voice_provider_error_and_exits_nonzero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _FailingVoiceProvider(_FakeVoiceProvider):
        def synthesize(self, request: SpeechRequest) -> SpeechResult:
            del request
            raise ProviderAuthenticationError("invalid API key")

    factory, _ = _provider_factory(_FakeTextGenerationProvider())
    voice_factory, _ = _voice_provider_factory(_FailingVoiceProvider())
    image_factory, _ = _image_provider_factory(_FakeImageProvider())

    exit_code = main(
        ["create", "story", "--topic", "Anything"],
        settings_loader=_settings_loader_with_all_api_keys,
        provider_factory=factory,
        voice_provider_factory=voice_factory,
        image_provider_factory=image_factory,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "fatal" in captured.err
    assert "invalid API key" in captured.err


def test_create_story_reports_image_provider_error_and_exits_nonzero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _FailingImageProvider(_FakeImageProvider):
        def generate(self, request: ImageRequest) -> ImageResult:
            del request
            raise ProviderAuthenticationError("invalid API key")

    factory, _ = _provider_factory(_FakeTextGenerationProvider())
    voice_factory, _ = _voice_provider_factory(_FakeVoiceProvider())
    image_factory, _ = _image_provider_factory(_FailingImageProvider())

    exit_code = main(
        ["create", "story", "--topic", "Anything"],
        settings_loader=_settings_loader_with_all_api_keys,
        provider_factory=factory,
        voice_provider_factory=voice_factory,
        image_provider_factory=image_factory,
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
    voice_factory, _ = _voice_provider_factory(_FakeVoiceProvider())
    image_factory, _ = _image_provider_factory(_FakeImageProvider())

    exit_code = main(
        ["create", "story", "--topic", "Anything"],
        settings_loader=_settings_loader_with_all_api_keys,
        provider_factory=factory,
        voice_provider_factory=voice_factory,
        image_provider_factory=image_factory,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "fatal" in captured.err


def test_create_story_rejects_empty_topic(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    provider = _FakeTextGenerationProvider()
    factory, _ = _provider_factory(provider)
    voice_provider = _FakeVoiceProvider()
    voice_factory, _ = _voice_provider_factory(voice_provider)
    image_provider = _FakeImageProvider()
    image_factory, _ = _image_provider_factory(image_provider)

    exit_code = main(
        ["create", "story", "--topic", "", "--output-dir", str(tmp_path)],
        settings_loader=_settings_loader_with_all_api_keys,
        provider_factory=factory,
        voice_provider_factory=voice_factory,
        image_provider_factory=image_factory,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "fatal" in captured.err
    assert "must not be empty" in captured.err
    # All three Providers still start and stop cleanly via the Runtime
    # -- the precondition fails inside the Workflow, after bootstrap
    # succeeds.
    assert provider.started
    assert provider.stopped
    assert voice_provider.started
    assert voice_provider.stopped
    assert image_provider.started
    assert image_provider.stopped
    # And nothing was written to disk -- the precondition fails before
    # `_save_narrated_story` is ever reached.
    assert list(tmp_path.iterdir()) == []


def test_create_requires_a_target() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["create"])

    assert exc_info.value.code != 0


def test_create_story_requires_topic() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["create", "story"])

    assert exc_info.value.code != 0


def test_default_provider_factory_builds_a_real_anthropic_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exercises `_default_text_generation_provider_factory`'s deferred
    import (ADR-0012) end to end through `main`, without a real network
    call: substitutes a fake in place of `AnthropicTextGenerationProvider`
    at the import site the factory resolves lazily -- the same boundary
    the real class would occupy."""
    provider = _FakeTextGenerationProvider("Only scene.")

    def _fake_anthropic_provider(*, api_key: str) -> _FakeTextGenerationProvider:
        del api_key
        return provider

    monkeypatch.setattr(
        "velora.providers.text_generation.AnthropicTextGenerationProvider",
        _fake_anthropic_provider,
    )

    voice_factory, _ = _voice_provider_factory(_FakeVoiceProvider())
    image_factory, _ = _image_provider_factory(_FakeImageProvider())

    exit_code = main(
        ["create", "story", "--topic", "Anything", "--output-dir", str(tmp_path)],
        settings_loader=_settings_loader_with_all_api_keys,
        voice_provider_factory=voice_factory,
        image_provider_factory=image_factory,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Only scene." in captured.out


def test_default_voice_provider_factory_builds_a_real_elevenlabs_provider(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercises `_default_voice_provider_factory`'s deferred import
    (ADR-0016) end to end through `main`, without a real network call:
    substitutes a fake in place of `ElevenLabsVoiceProvider` at the
    import site the factory resolves lazily -- the same boundary the
    real class would occupy."""
    provider = _FakeTextGenerationProvider("Only scene.")
    factory, _ = _provider_factory(provider)
    voice_provider = _FakeVoiceProvider()
    image_factory, _ = _image_provider_factory(_FakeImageProvider())

    def _fake_elevenlabs_provider(*, api_key: str) -> _FakeVoiceProvider:
        del api_key
        return voice_provider

    monkeypatch.setattr(
        "velora.providers.voice.ElevenLabsVoiceProvider",
        _fake_elevenlabs_provider,
    )

    exit_code = main(
        ["create", "story", "--topic", "Anything", "--output-dir", str(tmp_path)],
        settings_loader=_settings_loader_with_all_api_keys,
        provider_factory=factory,
        image_provider_factory=image_factory,
    )

    assert exit_code == 0
    assert voice_provider.started
    assert voice_provider.stopped


def test_default_image_provider_factory_builds_a_real_openai_provider(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercises `_default_image_provider_factory`'s deferred import
    (ADR-0019) end to end through `main`, without a real network call:
    substitutes a fake in place of `OpenAIImageProvider` at the import
    site the factory resolves lazily -- the same boundary the real
    class would occupy."""
    provider = _FakeTextGenerationProvider("Only scene.")
    factory, _ = _provider_factory(provider)
    voice_factory, _ = _voice_provider_factory(_FakeVoiceProvider())
    image_provider = _FakeImageProvider()

    def _fake_openai_provider(*, api_key: str) -> _FakeImageProvider:
        del api_key
        return image_provider

    monkeypatch.setattr(
        "velora.providers.image.OpenAIImageProvider",
        _fake_openai_provider,
    )

    exit_code = main(
        ["create", "story", "--topic", "Anything", "--output-dir", str(tmp_path)],
        settings_loader=_settings_loader_with_all_api_keys,
        provider_factory=factory,
        voice_provider_factory=voice_factory,
    )

    assert exit_code == 0
    assert image_provider.started
    assert image_provider.stopped
