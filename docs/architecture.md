# Arquitectura vigente

Este documento describe únicamente la arquitectura que existe hoy en el
repositorio. No describe fases futuras del roadmap; esas se documentan en
`PROJECT_CONTEXT.md` (estado), `docs/VISION.md` (visión de producto) y
los ADR (decisiones).

## Estado: Services — capacidad, dominio imagen (`ImageService`)

Fase completada: **Foundation** (PR-001), **Runtime** (PR-002),
**Configuration** (PR-003), **Logging** (PR-004), **Services —
infraestructura** (PR-005), **Providers — text_generation** (PR-006),
**Services — capacidad: NarrationService** (PR-007), **Engines —
StoryEngine** (PR-008), **Workflows — StoryWorkflow** (PR-009),
**Providers — dominio voice** (PR-010), **Services — capacidad:
VoiceService** (PR-011), **Engines — NarrationAudioEngine** (PR-012),
**Workflows — `StoryWorkflow` coordina ambos Engines** (PR-013),
**Providers — dominio image** (PR-014), **Services — capacidad:
ImageService** (PR-015). Fase siguiente: a decidir — un Engine de
imagen, extender `StoryWorkflow` una tercera vez, o persistir el audio
a disco desde la CLI. Ver `PROJECT_CONTEXT.md`.

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
    test_engines_*.py             # 4 archivos (más 2 de narration_audio)
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

### `velora.workflows.story`

El primer Workflow (ADR-0012), extendido desde PR-013 (ADR-0016) para
coordinar sus dos Engines:

- **`NarratedStory`** (`story: Story`, `audio: StoryAudio`) — compone
  el resultado de ambos Engines sin duplicar sus campos ni aplanarlos en
  un tipo nuevo; el mismo criterio de "reflejar, no reinventar" que
  ADR-0015 ya aplicó a `SceneAudio`/`StoryAudio`, aquí aplicado
  componiendo dos tipos existentes en vez de espejar uno.
- **`StoryWorkflow`** — envuelve un `StoryEngine` **y** un
  `NarrationAudioEngine`, ambos inyectados. `run(topic: str, *,
  max_tokens=1024) -> NarratedStory`: construye la `Story` con
  `StoryEngine.build_story()` y a continuación la sintetiza con
  `NarrationAudioEngine.synthesize()`, en ese orden — el único posible,
  ya que sintetizar necesita las escenas que el primer paso produce. Sin
  jerarquía de error propia: propaga `ValueError` (de `StoryEngine`) y
  `VeloraProviderError` (de cualquiera de los dos Providers subyacentes)
  tal cual. Sin resultado parcial: una falla sintetizando no devuelve
  ni la `Story` sola ni un `NarratedStory` con audio incompleto.

`velora.workflows` (raíz) no contiene nada todavía — ningún patrón
compartido entre Workflows ha justificado infraestructura en la raíz
(hay uno solo).

### `velora.cli`: `velora create story`

Primer subcomando real de la CLI, más allá del smoke-run de Runtime
(ADR-0012). Construye la cadena completa —
`AnthropicTextGenerationProvider` → `NarrationService` → `StoryEngine`,
y (desde PR-013, ADR-0016) `ElevenLabsVoiceProvider` → `VoiceService` →
`NarrationAudioEngine` — en el composition root, registrando ambos
Providers como `LifecycleComponent`s de un `Runtime` propio (distinto
del que usa el smoke-run por defecto). Requiere tanto
`VELORA_ANTHROPIC_API_KEY` como `VELORA_ELEVENLABS_API_KEY`
(`velora.configuration`, ambos campos opcionales — se validan en el
punto de uso, no al resolver Configuration; falla rápido si falta
cualquiera de las dos, antes de construir ningún Provider). Los imports
de `anthropic`, `elevenlabs`, `NarrationService`, `VoiceService`,
`StoryEngine`, `NarrationAudioEngine` y `StoryWorkflow` viven dentro de
las funciones que los usan, no a nivel de módulo: importar `velora.cli`
(y ejecutar cualquier comando distinto de `create story`) nunca
requiere los extras opcionales `velora[anthropic]` ni
`velora[elevenlabs]`. Imprime, por escena, el texto y una línea con el
tamaño en bytes y el formato del audio sintetizado — sin escribir
ningún archivo a disco todavía.

## Dependencias entre componentes

```
velora.cli  →  velora.runtime
velora.cli  →  velora.configuration
velora.cli  →  velora.logging  →  velora.runtime
velora.cli  →  velora.services
velora.cli  →  velora.workflows.story          (solo dentro de `create story`, import diferido)
velora.cli  →  velora.providers.text_generation  (solo dentro de `create story`, import diferido)
velora.cli  →  velora.providers.voice             (solo dentro de `create story`, import diferido)
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
velora.workflows.story  →  velora.engines.story
velora.workflows.story  →  velora.engines.narration_audio
```

`velora.engines.story` no importa `velora.providers` ni `anthropic` en
ningún punto — solo `velora.services.narration`, respetando el diagrama
canónico de ADR-0008. `velora.engines.narration_audio` sigue la misma
regla con `velora.services.voice`, y depende de `velora.engines.story`
únicamente para el tipo `Story` que recibe como entrada, no para
ninguna lógica. `velora.workflows.story` sigue la misma regla: solo
importa `velora.engines.story` y `velora.engines.narration_audio`,
nunca se salta una capa hacia `velora.services.*` o `velora.providers`
directamente. `velora.cli` construye la cadena completa, pero solo
dentro de la ejecución de `create story` — sus imports de
`velora.workflows.story`, `velora.providers.text_generation` y
`velora.providers.voice` están diferidos dentro de las funciones que
los usan, no a nivel de módulo (ADR-0012), precisamente para que el
resto de comandos de la CLI —y el propio `import velora.cli`— nunca
dependan de los extras `velora[anthropic]` ni `velora[elevenlabs]`.
`velora.engines.narration_audio` ya tiene un consumidor real:
`StoryWorkflow` lo coordina junto a `StoryEngine` desde PR-013
(ADR-0016). `velora.providers.image` (PR-014, ADR-0017) no aparece en
ninguna otra flecha del diagrama salvo la que lo une a
`velora.services.image` desde PR-015 (ADR-0018) — ningún
`velora.engines.*`, `velora.workflows.*`, ni `velora.cli`, importa
todavía `velora.providers.image` ni `velora.services.image`; ambos
siguen a la espera de un Engine real que los consuma.

## Lo que no existe todavía

Extensions. Tampoco existen más Providers de imagen (Flux, Stable
Diffusion, MidJourney), ni Providers de ningún otro dominio (video,
música, traducción); tampoco ningún Engine o Workflow que consuma
`velora.services.image`/`velora.providers.image` — ambos existen ya,
pero aislados. Más Engines (Subtitle, Timeline, Render, Publish — ver
`docs/VISION.md`), ni más Workflows que `StoryWorkflow`, siguen sin
existir. Ningún mecanismo para persistir a disco el audio que
`StoryWorkflow` produce — `create story` lo reporta (tamaño, formato),
no lo guarda. Cualquier mención a esas capas en otros documentos es
planificación, no arquitectura vigente. Este documento se actualizará
en cada PR que introduzca una capa o dominio nuevo.
