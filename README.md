# Velora

Velora es una plataforma pensada para evolucionar durante al menos diez
años sin que su Runtime necesite reescribirse. Prioriza estabilidad,
mantenibilidad y extensibilidad por encima de velocidad de desarrollo
inicial.

## Estado actual

**Fase: Engines — `SubtitleEngine` cronometra por duración real del audio** (PR-019). Ver
[`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) para el estado detallado,
[`docs/architecture.md`](docs/architecture.md) para la arquitectura
vigente, y [`docs/VISION.md`](docs/VISION.md) para la visión de producto.

## Requisitos

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) como gestor de dependencias

## Uso

```bash
git clone <repo>
cd velora
uv sync
uv run velora
```

```bash
uv run velora --version
uv run velora --help
```

`uv run velora`, sin flags, resuelve la configuración, configura el
logging, bootstrapea el Runtime, imprime su `runtime_id` de ejecución y
el entorno resuelto, y lo detiene de forma ordenada:

```
2026-08-02 19:24:08,315 INFO velora: runtime bootstrap starting
2026-08-02 19:24:08,316 INFO velora: runtime bootstrap completed
velora 0.1.0 — runtime 97811f88-8968-4a89-a392-c8b02a856fbb running (development).
2026-08-02 19:24:08,316 INFO velora: runtime shutdown starting
2026-08-02 19:24:08,316 INFO velora: runtime shutdown completed
velora 0.1.0 — runtime stopped cleanly.
```

(Las líneas `INFO ...` van a `stderr`; las líneas `velora 0.1.0 ...` van
a `stdout`.)

El entorno se controla con `VELORA_ENVIRONMENT`
(`development` por defecto, `staging`, o `production`), y la verbosidad
del log con `VELORA_LOG_LEVEL` (`debug`, `info` por defecto, `warning`,
`error`, `critical`):

```bash
VELORA_ENVIRONMENT=production VELORA_LOG_LEVEL=warning uv run velora
```

## Providers

Velora adapta APIs externas de IA detrás de contratos tipados por
dominio (`docs/VISION.md`). El primer dominio es `text_generation`:

```bash
pip install 'velora[anthropic]'
```

```python
from velora.providers.text_generation import (
    AnthropicTextGenerationProvider,
    Message,
    Role,
    TextGenerationRequest,
)
from velora.runtime import RuntimeContext
from datetime import datetime, UTC

provider = AnthropicTextGenerationProvider(api_key="sk-ant-...")
provider.start(RuntimeContext(runtime_id="manual", started_at=datetime.now(UTC)))

result = provider.generate(
    TextGenerationRequest(
        messages=[Message(role=Role.USER, content="Say hello in one word.")],
        max_tokens=10,
    )
)
print(result.text)

provider.stop(RuntimeContext(runtime_id="manual", started_at=datetime.now(UTC)))
```

(En uso real, `start`/`stop` los invoca `Runtime`, no se llaman a mano —
este ejemplo es solo para mostrar el contrato de forma aislada.)

Segundo dominio: `voice`, respaldado por ElevenLabs:

```bash
pip install 'velora[elevenlabs]'
```

```python
from velora.providers.voice import ElevenLabsVoiceProvider, SpeechRequest
from velora.runtime import RuntimeContext
from datetime import datetime, UTC

provider = ElevenLabsVoiceProvider(api_key="sk_...")
provider.start(RuntimeContext(runtime_id="manual", started_at=datetime.now(UTC)))

result = provider.synthesize(SpeechRequest(text="Hello from Velora."))
with open("hello.mp3", "wb") as f:
    f.write(result.audio)

provider.stop(RuntimeContext(runtime_id="manual", started_at=datetime.now(UTC)))
```

Consumido por `VoiceService`, `NarrationAudioEngine`, y
`StoryWorkflow` (dentro de `velora create story`) desde PR-011.

Tercer dominio: `image`, respaldado por OpenAI (DALL·E):

```bash
pip install 'velora[openai]'
```

```python
from velora.providers.image import OpenAIImageProvider, ImageRequest
from velora.runtime import RuntimeContext
from datetime import datetime, UTC

provider = OpenAIImageProvider(api_key="sk-...")
provider.start(RuntimeContext(runtime_id="manual", started_at=datetime.now(UTC)))

result = provider.generate(ImageRequest(prompt="a cat wearing a hat, watercolor style"))
with open("cat.png", "wb") as f:
    f.write(result.image)

provider.stop(RuntimeContext(runtime_id="manual", started_at=datetime.now(UTC)))
```

Sin consumidor todavía en `velora.services`; consumido por
`SceneImageEngine`, dentro de `StoryWorkflow`, desde PR-016.

## Services de capacidad

`NarrationService` es la primera capacidad construida sobre un
Provider — el llamador nunca sabe cuál (`docs/VISION.md`):

```python
from velora.services.narration import NarrationService

service = NarrationService(provider)  # cualquier TextGenerationProvider
result = service.narrate("Describe a city at dawn, in two sentences.")
print(result.text)
```

`VoiceService` es la segunda: mismo patrón, sobre `voice`:

```python
from velora.services.voice import VoiceService

voice_service = VoiceService(voice_provider)  # cualquier VoiceProvider
speech = voice_service.speak("Describe a city at dawn, in two sentences.")
with open("dawn.mp3", "wb") as f:
    f.write(speech.audio)
```

Consumido por `NarrationAudioEngine`, dentro de `StoryWorkflow`, desde
PR-012.

`ImageService` es la tercera: mismo patrón, sobre `image`:

```python
from velora.services.image import ImageService

image_service = ImageService(image_provider)  # cualquier ImageProvider
picture = image_service.draw("A city skyline at dawn, watercolor style.")
with open("dawn.png", "wb") as f:
    f.write(picture.image)
```

Consumido por `SceneImageEngine`, dentro de `StoryWorkflow`, desde
PR-016.

## Engines

`StoryEngine` es el primer Engine: genera narración vía un
`NarrationService` inyectado y la divide en escenas por párrafos:

```python
from velora.engines.story import StoryEngine

engine = StoryEngine(service)  # el mismo NarrationService de arriba
story = engine.build_story("The history of the printing press")

for scene in story.scenes:
    print(f"[{scene.index}] {scene.text}")
```

`NarrationAudioEngine` es el segundo: sintetiza cada escena de una
`Story` en audio, vía un `VoiceService` inyectado:

```python
from velora.engines.narration_audio import NarrationAudioEngine

audio_engine = NarrationAudioEngine(voice_service)  # el mismo VoiceService de arriba
story_audio = audio_engine.synthesize(story)  # la misma Story de arriba

for scene_audio in story_audio.scenes:
    with open(f"scene_{scene_audio.index}.{scene_audio.audio_format}", "wb") as f:
        f.write(scene_audio.audio)
```

`SceneImageEngine` es el tercero: genera una imagen por escena de una
`Story`, vía un `ImageService` inyectado:

```python
from velora.engines.scene_image import SceneImageEngine

image_engine = SceneImageEngine(image_service)  # el mismo ImageService de arriba
story_images = image_engine.illustrate(story)  # la misma Story de arriba

for scene_image in story_images.scenes:
    with open(f"scene_{scene_image.index}.{scene_image.image_format}", "wb") as f:
        f.write(scene_image.image)
```

`SubtitleEngine` es el cuarto, y el único sin Provider ni Service — no
llama a nada externo. Cronometra cada escena con la duración real de su
audio ya generado:

```python
from velora.engines.subtitle import SubtitleEngine, render_srt

subtitle_engine = SubtitleEngine()  # sin Service, sin Provider
story_subtitles = subtitle_engine.caption(story, story_audio)  # Story y StoryAudio de arriba

with open("story.srt", "w", encoding="utf-8") as f:
    f.write(render_srt(story_subtitles))
```

`words_per_minute` (por defecto `150.0`) es un *fallback*, no el método
principal: solo se usa si la duración de una escena en particular no
puede medirse desde su audio (formato no soportado, o corrupto).

## Workflows

`StoryWorkflow` es el primer Workflow, y desde PR-018 coordina los
cuatro Engines de arriba: envuelve un `StoryEngine`, un
`NarrationAudioEngine`, un `SceneImageEngine`, y un `SubtitleEngine`
inyectados, y ejecuta el pipeline completo (`docs/VISION.md`: "Los
Workflows conectan todos los motores"):

```python
from velora.workflows.story import StoryWorkflow

# los mismos Engines de arriba
workflow = StoryWorkflow(engine, audio_engine, image_engine, subtitle_engine)
narrated_story = workflow.run("The history of the printing press")

story = narrated_story.story
story_audio = narrated_story.audio
story_images = narrated_story.images
story_subtitles = narrated_story.subtitles  # cronometrados por la duración real de story_audio
```

También es el primer subcomando real de la CLI, más allá del smoke-run
de Runtime — y, desde PR-017, persiste su resultado a disco:

```bash
VELORA_ANTHROPIC_API_KEY=sk-ant-... \
VELORA_ELEVENLABS_API_KEY=... \
VELORA_OPENAI_API_KEY=sk-... \
uv run velora create story --topic "The history of the printing press" \
    --output-dir ./output
```

```
Story: The history of the printing press (3 scene(s))
Saved to: output/3f2a9e1c-...
Subtitles: story.srt

[0] ...
    audio: scene_000.mp3
    image: scene_000.png
[1] ...
    audio: scene_001.mp3
    image: scene_001.png
[2] ...
    audio: scene_002.mp3
    image: scene_002.png
```

`SubtitleEngine` no requiere ninguna clave de API adicional. Desde
PR-019, el tiempo de cada subtítulo se mide directamente de la
duración real del audio generado; `--words-per-minute` (por defecto,
`150.0`) solo aplica como reserva para una escena cuya duración no
pueda medirse.

`--output-dir` es opcional (por defecto, el directorio actual). Cada
ejecución crea su propio subdirectorio, nombrado con el `runtime_id` de
esa ejecución, así que ejecuciones sucesivas con el mismo
`--output-dir` nunca se pisan entre sí. Dentro de ese subdirectorio:
`story.txt` (la transcripción completa) y un archivo de audio y uno de
imagen por escena.

## Desarrollo

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

`uv run` garantiza que el comando se ejecuta con el intérprete y las
dependencias de `.venv/` del proyecto, sin importar si el entorno virtual
está activado en la shell actual. Si prefieres no escribir `uv run` cada
vez, activa el entorno explícitamente (`source .venv/bin/activate` en
Linux/macOS) y a partir de ahí `pytest`, `ruff` y `mypy` sueltos también
funcionarán.

## Filosofía

- Runtime First
- Stable Core
- Dependency Injection
- Composition over Inheritance
- Configuration over Code
- Typed Everything
- Explicit APIs
- Small Public Surface
- Fail Fast
- No Hidden Magic

Ver [`docs/architecture.md`](docs/architecture.md) para el detalle y
[`docs/adr/`](docs/adr/) para el historial de decisiones.

## Roadmap

```
Foundation → Runtime → Configuration → Logging → Services →
Providers → Engines → Workflows → Extensions
```

Este orden está congelado: cada fase solo depende de las anteriores.

## Licencia

MIT — ver [`LICENSE`](LICENSE).
