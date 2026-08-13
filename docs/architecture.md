# Arquitectura vigente

Este documento describe únicamente la arquitectura que existe hoy en el
repositorio. No describe fases futuras del roadmap; esas se documentan en
`PROJECT_CONTEXT.md` (estado), `docs/VISION.md` (visión de producto) y
los ADR (decisiones).

## Estado: Engines — `SubtitleEngine` cronometra por duración real del audio

Fase completada: **Foundation** (PR-001), **Runtime** (PR-002),
**Configuration** (PR-003), **Logging** (PR-004), **Services —
infraestructura** (PR-005), **Providers — text_generation** (PR-006),
**Services — capacidad: NarrationService** (PR-007), **Engines —
StoryEngine** (PR-008), **Workflows — StoryWorkflow** (PR-009),
**Providers — dominio voice** (PR-010), **Services — capacidad:
VoiceService** (PR-011), **Engines — NarrationAudioEngine** (PR-012),
**Workflows — `StoryWorkflow` coordina ambos Engines** (PR-013),
**Providers — dominio image** (PR-014), **Services — capacidad:
ImageService** (PR-015), **Engines — SceneImageEngine; Workflows —
`StoryWorkflow` coordina los tres Engines** (PR-016), **CLI —
persistencia a disco** (PR-017), **Engines — SubtitleEngine; Workflows
— `StoryWorkflow` coordina los cuatro Engines; CLI — persiste
`story.srt`** (PR-018), **Engines — `SubtitleEngine` mide la duración
real del audio en vez de estimarla** (PR-019). El pipeline de `create
story` cubre ahora los cuatro Engines del pipeline de ejemplo de
`docs/VISION.md` hasta "insertar subtítulos", con subtítulos
cronometrados con precisión sobre el audio real generado. Fase
siguiente: a decidir — un Timeline Engine, o un cuarto dominio de
Provider. Ver `PROJECT_CONTEXT.md`.

## Estructura del repositorio

```
src/velora/
    __init__.py           # Metadata pública del paquete (__version__)
    cli.py                 # Entrypoint de consola `velora` (composition root)
    py.typed               # Marcador PEP 561: el paquete está tipado
    configuration/           # Ver secciones anteriores de este documento
    logging/                 # (sin cambios en este PR)
    services/                 # Clock, IdGenerator (infraestructura, PR-005)
        narration/               # NarrationService (capacidad, PR-007)
        voice/                     # VoiceService (capacidad, PR-011)
        image/                       # ImageService (capacidad, PR-015)
    runtime/                   # (sin cambios funcionales en este PR)
    providers/
        __init__.py         # Jerarquía de error compartida entre dominios
        _errors.py            # VeloraProviderError y su jerarquía
        text_generation/
            __init__.py         # Superficie pública del dominio
            _types.py             # Role, Message, TextGenerationRequest/Result
            _protocol.py            # TextGenerationProvider
            _anthropic.py             # AnthropicTextGenerationProvider (real, requiere extra)
        voice/
            __init__.py         # Superficie pública del dominio
            _types.py             # SpeechRequest, SpeechResult
            _protocol.py            # VoiceProvider
            _elevenlabs.py            # ElevenLabsVoiceProvider (real, requiere extra)
        image/
            __init__.py         # Superficie pública del dominio
            _types.py             # ImageRequest, ImageResult
            _protocol.py            # ImageProvider
            _openai.py                # OpenAIImageProvider (real, requiere extra)
    engines/
        __init__.py         # Namespace, sin lógica compartida todavía
        story/
            __init__.py         # Superficie pública del Story Engine
            _types.py              # Scene, Story
            _engine.py               # StoryEngine
        narration_audio/
            __init__.py         # Superficie pública del Narration Audio Engine
            _types.py              # SceneAudio, StoryAudio
            _engine.py               # NarrationAudioEngine
        scene_image/
            __init__.py         # Superficie pública del Scene Image Engine
            _types.py              # SceneImage, StoryImages
            _engine.py               # SceneImageEngine
        subtitle/
            __init__.py         # Superficie pública del Subtitle Engine
            _types.py              # SceneSubtitle, StorySubtitles
            _engine.py               # SubtitleEngine
            _duration.py             # measure_duration_seconds
            _srt.py                  # render_srt
    workflows/
        __init__.py         # Namespace, sin lógica compartida todavía
        story/
            __init__.py         # Superficie pública del Story Workflow
            _types.py              # NarratedStory
            _workflow.py           # StoryWorkflow
tests/
    test_package_metadata.py
    test_cli.py
    test_configuration_*.py       # 8 archivos
    test_logging_*.py             # 5 archivos
    test_runtime_*.py             # 8 archivos
    test_services_*.py            # 4 archivos (incluye narration, voice, image)
    test_providers_*.py           # 4 archivos (más 3 de voice, más 3 de image)
    test_engines_*.py             # 4 archivos (más 2 de narration_audio, más 2 de
                                   # scene_image, más 4 de subtitle)
    test_workflows_*.py           # 1 archivo
    test_no_direct_environ_access.py     # invariante ejecutable
docs/
    architecture.md               # Este documento
    VISION.md                       # Visión de producto
    adr/                              # Registro de decisiones arquitectónicas
PROJECT_CONTEXT.md                  # Estado actual del proyecto
```

## Componentes existentes

### `velora`, `velora.configuration`, `velora.logging`, `velora.runtime`, `velora.services`

Sin cambios funcionales de superficie pública en este PR, salvo:
`velora.runtime` expone también `Clock`/`SystemClock`/`IdGenerator`/
`UUIDIdGenerator` (desde PR-005). Ver el ADR correspondiente de cada uno
(ADR-0001 a ADR-0007) para el detalle completo.

### `velora.providers`

Paquete raíz: solo la jerarquía de error compartida entre dominios
(ADR-0009):

- **`VeloraProviderError`** (base) → `ProviderAuthenticationError`,
  `ProviderRateLimitError`, `ProviderConnectionError`,
  `ProviderRequestError`.

No contiene lógica ni contratos de dominio — esos viven en cada
subpaquete de dominio.

### `velora.providers.text_generation`

Primer dominio de Provider (ADR-0009: dominio propio, no un `Provider`
genérico):

- **`TextGenerationProvider`** — el único contrato que el resto del
  sistema conocerá (`NarrationService`, más abajo, depende de esto,
  nunca de una clase concreta). Síncrono, sin streaming (deliberado —
  ver ADR-0009).
- **`Message`**, **`Role`** (`USER`/`ASSISTANT`), **`TextGenerationRequest`**
  (`messages`, `max_tokens`, `system`, `temperature`),
  **`TextGenerationResult`** (`text`, `stop_reason`, `input_tokens`,
  `output_tokens`) — provider-agnósticos, no mencionan a ningún vendor.
- **`AnthropicTextGenerationProvider`** — primera implementación real.
  Implementa `~velora.runtime.LifecycleComponent`: `start()` construye
  el cliente del SDK (pool de conexiones HTTP real); `stop()` lo cierra
  — el primer implementador no trivial de ese contrato en el código
  base. Traduce las excepciones propias del SDK de Anthropic
  (`AuthenticationError`, `RateLimitError`, `APIConnectionError`,
  `APIStatusError`) a la jerarquía compartida de `velora.providers`;
  quien llama a `generate()` nunca ve un tipo de excepción de
  `anthropic`. Requiere el extra opcional `velora[anthropic]` — no es
  una dependencia obligatoria de `velora`.

### `velora.providers.voice`

Segundo dominio de Provider (ADR-0013), mismo patrón que
`text_generation` (ADR-0009):

- **`VoiceProvider`** — el único contrato que el resto del sistema
  conocerá. Síncrono, sin streaming, misma razón que `text_generation`.
- **`SpeechRequest`** (`text`) — deliberadamente mínimo, un solo campo;
  la elección de voz vive en el Provider (constructor), no en el
  request. **`SpeechResult`** (`audio: bytes`, `audio_format: str`) —
  `audio_format` es un `str` plano, no un enum: solo existe un valor
  real (`"mp3"`) hasta que un segundo Provider produzca otro.
- **`ElevenLabsVoiceProvider`** — primera implementación real.
  Implementa `~velora.runtime.LifecycleComponent`: `start()` construye
  su propio `httpx.Client` y se lo inyecta al SDK; `stop()` lo cierra —
  evita depender de la estructura interna del SDK para el cierre. El SDK
  de `elevenlabs` no distingue clases de excepción por código HTTP más
  allá de 422 (`UnprocessableEntityError`); `synthesize()` inspecciona
  `status_code` en la `ApiError` genérica para distinguir 401/429/otros,
  y captura `httpx.HTTPError` por separado para fallos de conexión (el
  SDK no los envuelve). Requiere el extra opcional `velora[elevenlabs]`
  — independiente de `velora[anthropic]`.

### `velora.providers.image`

Tercer dominio de Provider (ADR-0017), mismo patrón que
`text_generation` y `voice`:

- **`ImageProvider`** — el único contrato que el resto del sistema
  conocerá. Síncrono, sin streaming, misma razón que los otros dos
  dominios.
- **`ImageRequest`** (`prompt`) — deliberadamente mínimo, un solo campo;
  modelo, tamaño y calidad viven en el Provider (constructor), no en el
  request. **`ImageResult`** (`image: bytes`, `image_format: str`) —
  `image_format` es un `str` plano, no un enum: solo existe un valor
  real (`"png"`) hasta que un segundo Provider produzca otro.
- **`OpenAIImageProvider`** — primera implementación real, respaldada
  por la API de imágenes de OpenAI (DALL·E). Implementa
  `~velora.runtime.LifecycleComponent`: `start()` construye su propio
  `httpx.Client` y se lo inyecta al SDK; `stop()` lo cierra — mismo
  patrón que `ElevenLabsVoiceProvider`. A diferencia de `elevenlabs`, el
  SDK de `openai` sí distingue clases de excepción por categoría
  (`AuthenticationError`, `RateLimitError`, `APIConnectionError`,
  `APIStatusError`) — mismo mapeo 1:1 por tipo que
  `AnthropicTextGenerationProvider` ya usa, no por `status_code`.
  Solicita el formato de respuesta `b64_json` y lo decodifica a `bytes`
  antes de devolverlo — nunca expone una URL temporal como resultado.
  Requiere el extra opcional `velora[openai]` — independiente de
  `velora[anthropic]` y `velora[elevenlabs]`.

Sin consumidor todavía en `velora.services`, `velora.engines`, ni
`velora.workflows` — este PR es horizontal (ADR-0017), no conectado
verticalmente a ningún Service o Engine.

### `velora.services.narration`

El primer Service de capacidad (ADR-0008, ADR-0010):

- **`NarrationService`** — envuelve un `TextGenerationProvider`
  inyectado. `narrate(instructions: str, *, max_tokens=1024) ->
  TextGenerationResult`. Deliberadamente delgado: no decide estructura
  narrativa ni tono más allá de un system prompt genérico (eso
  pertenece a un futuro Engine). No implementa `LifecycleComponent` — no
  tiene recurso propio; el Provider inyectado gestiona el suyo. Rechaza
  instrucciones vacías con `ValueError` (única precondición; no
  justifica una jerarquía de error propia todavía).

Vive en un subpaquete de `velora.services`, no en la raíz: importar
`Clock`/`IdGenerator` nunca debe arrastrar `velora.providers` para quien
no lo necesita.

### `velora.services.voice`

Segundo Service de capacidad (ADR-0014), mismo patrón que
`velora.services.narration`:

- **`VoiceService`** — envuelve un `VoiceProvider` inyectado.
  `speak(text: str) -> SpeechResult`. Sin parámetro de configuración
  por defecto (a diferencia de `system_prompt` en `NarrationService`:
  síntesis de voz no tiene un equivalente natural). Reutiliza
  `SpeechResult` directamente. Rechaza `text` vacío con `ValueError`.

Consumido por `NarrationAudioEngine` desde PR-012 (ADR-0015) —
`StoryEngine` no lo conoce; solo `NarrationAudioEngine`, dentro de
`StoryWorkflow`, lo hace.

### `velora.services.image`

Tercer Service de capacidad (ADR-0018), mismo patrón que
`velora.services.narration` y `velora.services.voice`:

- **`ImageService`** — envuelve un `ImageProvider` inyectado.
  `draw(prompt: str) -> ImageResult`. Nombrado `draw`, no `generate`,
  únicamente para no colisionar léxicamente con
  `ImageProvider.generate()` en el mismo call stack — sin diferencia
  semántica. Sin parámetro de configuración por defecto, mismo motivo
  que `VoiceService`. Reutiliza `ImageResult` directamente. Rechaza
  `prompt` vacío con `ValueError`.

Sin consumidor todavía en `velora.engines` ni `velora.workflows` —
mismo estado en el que estuvo `VoiceService` entre PR-011 y PR-012.

### `velora.engines.story`

El primer Engine (ADR-0011):

- **`Scene`** (`index`, `text`), **`Story`** (`topic`, `scenes`) — tipos
  producidos, no consumidos, por este Engine; `scenes` puede ser vacío
  (estado válido, no error).
- **`StoryEngine`** — envuelve un `NarrationService` inyectado.
  `build_story(topic: str, *, max_tokens=1024) -> Story`. Genera
  narración vía el Service y la divide en escenas por párrafos (líneas
  en blanco) — división determinista, no dependiente de que el modelo
  siga un formato de delimitador pedido. Sin control de número de
  escenas (fuera de alcance deliberado). Rechaza `topic` vacío con
  `ValueError`.

`velora.engines` (raíz) no contiene nada todavía — ningún patrón
compartido entre `StoryEngine` y `NarrationAudioEngine` ha justificado
todavía infraestructura en la raíz (más allá de que ambos dependen de un
Service de capacidad distinto, ya reflejado en cada Engine por separado,
no en un tipo o utilidad compartida).

### `velora.engines.narration_audio`

Segundo Engine (ADR-0015):

- **`SceneAudio`** (`index`, `audio: bytes`, `audio_format: str`),
  **`StoryAudio`** (`topic`, `scenes`) — el reflejo en audio de
  `Scene`/`Story`; `SceneAudio` no repite el texto de la escena (el
  `index` basta para correlacionarlo con la `Story` original que el
  llamador ya tiene).
- **`NarrationAudioEngine`** — envuelve un `VoiceService` inyectado.
  `synthesize(story: Story) -> StoryAudio`. A diferencia de
  `StoryEngine`, no tiene ninguna precondición propia que verificar: su
  entrada (`Story`) ya llegó validada por la capa anterior. Sin
  agregación de errores — la primera escena que falle detiene toda la
  operación, propagando la excepción del Provider subyacente tal cual.

### `velora.engines.scene_image`

Tercer Engine (ADR-0019), mismo patrón exacto que
`velora.engines.narration_audio`:

- **`SceneImage`** (`index`, `image: bytes`, `image_format: str`) —
  igual que `SceneAudio`, no repite el texto de la escena. **`StoryImages`**
  (`topic`, `scenes`) — nombrado en plural, a diferencia de
  `StoryAudio`: "imágenes" es un sustantivo contable (una por escena),
  "audio" no.
- **`SceneImageEngine`** — envuelve un `ImageService` inyectado.
  `illustrate(story: Story) -> StoryImages`. Misma ausencia de
  precondición propia y de agregación de errores que
  `NarrationAudioEngine`. Usa el texto de cada escena como prompt, sin
  reescritura ni ingeniería de prompt — no hay todavía ningún
  consumidor real que necesite esa traducción.

### `velora.engines.subtitle`

Cuarto Engine (ADR-0021), sin Service inyectado — no llama a ningún
Provider directamente. Desde PR-019 (ADR-0022), depende del tipo
`StoryAudio` de `velora.engines.narration_audio` para cronometrar sus
subtítulos con precisión:

- **`SceneSubtitle`** (`index`, `text: str`, `start_seconds: float`,
  `end_seconds: float`) — a diferencia de `SceneAudio`/`SceneImage`, sí
  repite el texto de la escena: el texto *es* el artefacto, no hay un
  payload binario que lo sustituya. **`StorySubtitles`** (`topic`,
  `scenes`).
- **`measure_duration_seconds(audio: bytes) -> float | None`**
  (`velora.engines.subtitle._duration`) — mide la duración real de un
  clip de audio vía `mutagen` (lee metadata del contenedor, sin
  decodificar el audio completo; detecta el formato por sus propios
  bytes mágicos, sin necesitar nombre de archivo). Devuelve `None` —
  nunca lanza — si `mutagen` no puede interpretar el audio (formato no
  soportado, corrupto, o bytes que no son audio). `mutagen` es la
  primera dependencia base no opcional del proyecto (ADR-0022):
  distinta categoría que `anthropic`/`elevenlabs`/`openai` (SDKs de
  proveedores intercambiables, extras opcionales) — es infraestructura
  genérica sin vendor lock-in que el propio Core necesita.
- **`SubtitleEngine`** — constructor recibe `words_per_minute: float =
  150.0`, ahora un *fallback*, no el método principal de cronometraje.
  `caption(story: Story, audio: StoryAudio) -> StorySubtitles`: para
  cada escena, busca el `SceneAudio` correspondiente por `index` y mide
  su duración real; si no existe o no puede medirse, cae al estimado
  por conteo de palabras. Back-to-back sin separación entre escenas.
  Única fuente de error: `ValueError` si `words_per_minute` no es
  positivo, validado en el constructor — `caption()` en sí nunca lanza.
- **`render_srt(subtitles: StorySubtitles) -> str`** — renderiza a
  formato SubRip (`.srt`), como función separada del tipo de resultado
  (`velora.engines.subtitle._srt`): el Engine no decide el formato de
  salida.

### `velora.workflows.story`

El primer Workflow (ADR-0012), extendido desde PR-013 (ADR-0016) para
coordinar dos Engines, desde PR-016 (ADR-0019) para coordinar tres, y
desde PR-018 (ADR-0021) para coordinar los cuatro:

- **`NarratedStory`** (`story: Story`, `audio: StoryAudio`, `images:
  StoryImages`, `subtitles: StorySubtitles`) — compone el resultado de
  los cuatro Engines sin duplicar sus campos ni aplanarlos en un tipo
  nuevo; el mismo criterio de "reflejar, no reinventar" que ADR-0015 ya
  aplicó a `SceneAudio`/`StoryAudio`, aquí aplicado componiendo cuatro
  tipos existentes en vez de espejar uno.
- **`StoryWorkflow`** — envuelve un `StoryEngine`, un
  `NarrationAudioEngine`, un `SceneImageEngine`, **y** un
  `SubtitleEngine`, los cuatro inyectados. `run(topic: str, *,
  max_tokens=1024) -> NarratedStory`: construye la `Story` con
  `StoryEngine.build_story()`, la sintetiza, la ilustra, y la subtitula,
  en ese orden. Desde PR-019 (ADR-0022), el subtitulado deja de ser
  independiente de la síntesis: `caption()` necesita el `StoryAudio` ya
  producido para cronometrarse contra él, así que debe ejecutarse
  después de `synthesize()` — sigue sin depender de la ilustración. Sin
  jerarquía de error propia: propaga `ValueError` (de `StoryEngine`) y
  `VeloraProviderError` (de cualquiera de los tres Providers
  subyacentes — el subtitulado no puede fallar así, no tiene Provider)
  tal cual. Sin resultado parcial: una falla en cualquier paso no
  devuelve ni la `Story` sola ni un `NarratedStory` incompleto.

`velora.workflows` (raíz) no contiene nada todavía — ningún patrón
compartido entre Workflows ha justificado infraestructura en la raíz
(hay uno solo).

### `velora.cli`: `velora create story`

Primer subcomando real de la CLI, más allá del smoke-run de Runtime
(ADR-0012). Construye la cadena completa —
`AnthropicTextGenerationProvider` → `NarrationService` → `StoryEngine`,
`ElevenLabsVoiceProvider` → `VoiceService` → `NarrationAudioEngine`
(desde PR-013, ADR-0016), `OpenAIImageProvider` → `ImageService` →
`SceneImageEngine` (desde PR-016, ADR-0019), y `SubtitleEngine`
directamente, sin Provider ni Service (desde PR-018, ADR-0021) — en el
composition root, registrando los tres Providers (no cuatro:
`SubtitleEngine` no tiene uno) como `LifecycleComponent`s de un
`Runtime` propio (distinto del que usa el smoke-run por defecto).
Requiere `VELORA_ANTHROPIC_API_KEY`, `VELORA_ELEVENLABS_API_KEY`, **y**
`VELORA_OPENAI_API_KEY` (`velora.configuration`, los tres campos
opcionales — se validan en el punto de uso, no al resolver
Configuration; falla rápido si falta cualquiera de las tres, antes de
construir ningún Provider) — sin ninguna clave nueva para
`SubtitleEngine`. Gana el argumento `--words-per-minute` (por defecto
`150.0`), que desde PR-019 (ADR-0022) documenta explícitamente que es
un ritmo de reserva, usado solo cuando la duración de una escena no
puede medirse desde su audio generado. Los imports de `anthropic`,
`elevenlabs`, `openai`, `NarrationService`, `VoiceService`,
`ImageService`, `StoryEngine`, `NarrationAudioEngine`,
`SceneImageEngine`, `SubtitleEngine`, y `StoryWorkflow` viven dentro de
las funciones que los usan, no a nivel de módulo: importar `velora.cli`
(y ejecutar cualquier comando distinto de `create story`) nunca
requiere los extras opcionales `velora[anthropic]`, `velora[elevenlabs]`, ni
`velora[openai]`.

Desde PR-017 (ADR-0020), persiste su resultado a disco:
`_save_narrated_story` escribe, bajo `<--output-dir>/<runtime_id>/`
(`--output-dir` por defecto `.`; `runtime_id` es el mismo id que el
`Runtime` de esa ejecución ya genera), un `story.txt` con la
transcripción, un archivo `scene_{index:03d}.{formato}` por escena
para audio y otro para imagen, y (desde PR-018, ADR-0021) un único
`story.srt` compartido (no uno por escena — un archivo `.srt` ya
contiene sus propios límites de escena como cues numerados). Ocurre
después de que `StoryWorkflow` completa con éxito y antes de imprimir
cualquier salida — lo impreso describe lo ya escrito. Un `OSError` al
persistir se reporta como `fatal`, igual que cualquier otro fallo de
este comando. Imprime el nombre del archivo de subtítulos, y, por
escena, el texto y los nombres de los dos archivos guardados (audio e
imagen), y la ruta completa del directorio de esa ejecución.

## Dependencias entre componentes

```
velora.cli  →  velora.runtime
velora.cli  →  velora.configuration
velora.cli  →  velora.logging  →  velora.runtime
velora.cli  →  velora.services
velora.cli  →  velora.workflows.story          (solo dentro de `create story`, import diferido)
velora.cli  →  velora.providers.text_generation  (solo dentro de `create story`, import diferido)
velora.cli  →  velora.providers.voice             (solo dentro de `create story`, import diferido)
velora.cli  →  velora.providers.image              (solo dentro de `create story`, import diferido)
velora.providers.text_generation  →  velora.runtime   (solo para LifecycleComponent)
velora.providers.text_generation  →  velora.providers  (jerarquía de error)
velora.providers.text_generation._anthropic  →  anthropic (extra opcional)
velora.providers.voice  →  velora.runtime   (solo para LifecycleComponent)
velora.providers.voice  →  velora.providers  (jerarquía de error)
velora.providers.voice._elevenlabs  →  elevenlabs, httpx (extra opcional)
velora.providers.image  →  velora.runtime   (solo para LifecycleComponent)
velora.providers.image  →  velora.providers  (jerarquía de error)
velora.providers.image._openai  →  openai, httpx (extra opcional)
velora.services.narration  →  velora.providers.text_generation
velora.services.voice  →  velora.providers.voice
velora.services.image  →  velora.providers.image
velora.engines.story  →  velora.services.narration
velora.engines.narration_audio  →  velora.services.voice
velora.engines.narration_audio  →  velora.engines.story  (solo el tipo `Story`)
velora.engines.scene_image  →  velora.services.image
velora.engines.scene_image  →  velora.engines.story  (solo el tipo `Story`)
velora.engines.subtitle  →  velora.engines.story  (solo el tipo `Story`)
velora.engines.subtitle  →  velora.engines.narration_audio  (solo el tipo `StoryAudio`, desde PR-019)
velora.engines.subtitle._duration  →  mutagen (dependencia base, no extra)
velora.workflows.story  →  velora.engines.story
velora.workflows.story  →  velora.engines.narration_audio
velora.workflows.story  →  velora.engines.scene_image
velora.workflows.story  →  velora.engines.subtitle
```

`velora.engines.story` no importa `velora.providers` ni `anthropic` en
ningún punto — solo `velora.services.narration`, respetando el diagrama
canónico de ADR-0008. `velora.engines.narration_audio` y
`velora.engines.scene_image` siguen la misma regla con
`velora.services.voice` y `velora.services.image` respectivamente, y
ambos dependen de `velora.engines.story` únicamente para el tipo
`Story` que reciben como entrada, no para ninguna lógica.
`velora.engines.subtitle` no depende de ningún `velora.services.*` en
absoluto — solo de `velora.engines.story` (por `Story`) y, desde PR-019
(ADR-0022), de `velora.engines.narration_audio` (por `StoryAudio`, el
único caso en todo `velora.engines` donde un Engine depende del tipo de
resultado de *otro* Engine, no solo de `Story`) — sigue sin depender de
ningún Service ni Provider (ADR-0021).
`velora.workflows.story` sigue la misma regla: solo importa
`velora.engines.story`, `velora.engines.narration_audio`,
`velora.engines.scene_image`, y `velora.engines.subtitle`, nunca se
salta una capa hacia `velora.services.*` o `velora.providers`
directamente. `velora.cli` construye la cadena completa, pero solo
dentro de la ejecución de `create story` — sus imports de
`velora.workflows.story`, `velora.providers.text_generation`,
`velora.providers.voice`, y `velora.providers.image` están diferidos
dentro de las funciones que los usan, no a nivel de módulo (ADR-0012),
precisamente para que el resto de comandos de la CLI —y el propio
`import velora.cli`— nunca dependan de los extras `velora[anthropic]`,
`velora[elevenlabs]`, ni `velora[openai]`. `velora.engines.
narration_audio`, `velora.engines.scene_image`, y `velora.engines.
subtitle` tienen ya, los tres, un consumidor real: `StoryWorkflow`
coordina los cuatro Engines desde PR-018 (ADR-0021).
`velora.providers.image`/`velora.services.image` (PR-014/PR-015,
ADR-0017/ADR-0018) dejaron de estar aislados desde PR-016: ahora
alcanzan al resto del sistema a través de `SceneImageEngine`.

## Lo que no existe todavía

Extensions. Tampoco existen más Providers de imagen (Flux, Stable
Diffusion, MidJourney), ni Providers de ningún otro dominio (video,
música, traducción). Más Engines (Timeline, Render, Publish — ver
`docs/VISION.md`), ni más Workflows que `StoryWorkflow`, siguen sin
existir. Ningún mecanismo para reanudar o reutilizar una ejecución
anterior de `create story` desde su directorio ya guardado — cada
ejecución es independiente. Cualquier mención a esas capas en otros
documentos es planificación, no arquitectura vigente. Este documento se
actualizará en cada PR que
introduzca una capa o dominio nuevo.
