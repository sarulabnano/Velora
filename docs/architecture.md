# Arquitectura vigente

Este documento describe únicamente la arquitectura que existe hoy en el
repositorio. No describe fases futuras del roadmap; esas se documentan en
`PROJECT_CONTEXT.md` (estado), `docs/VISION.md` (visión de producto) y
los ADR (decisiones).

## Estado: Engines — `NarrationAudioEngine`

Fase completada: **Foundation** (PR-001), **Runtime** (PR-002),
**Configuration** (PR-003), **Logging** (PR-004), **Services —
infraestructura** (PR-005), **Providers — text_generation** (PR-006),
**Services — capacidad: NarrationService** (PR-007), **Engines —
StoryEngine** (PR-008), **Workflows — StoryWorkflow** (PR-009),
**Providers — dominio voice** (PR-010), **Services — capacidad:
VoiceService** (PR-011), **Engines — NarrationAudioEngine** (PR-012).
Fase siguiente: a decidir — extender `StoryWorkflow` (o un Workflow
nuevo) para coordinar `StoryEngine` y `NarrationAudioEngine`, o más
dominios de Providers/Services.

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
            _workflow.py           # StoryWorkflow
tests/
    test_package_metadata.py
    test_cli.py
    test_configuration_*.py       # 8 archivos
    test_logging_*.py             # 5 archivos
    test_runtime_*.py             # 8 archivos
    test_services_*.py            # 4 archivos (incluye narration, voice)
    test_providers_*.py           # 4 archivos (más 3 de voice)
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

Ningún Engine o Workflow existente lo usa todavía —
`StoryEngine`/`StoryWorkflow` no lo conocen.

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

`velora.engines` (raíz) no contiene nada todavía — ningún segundo Engine
ha revelado una necesidad compartida real que justifique infraestructura
en la raíz.

#`velora.engines` (raíz) no contiene nada todavía — ningún patrón
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

El primer Workflow (ADR-0012):

- **`StoryWorkflow`** — envuelve un `StoryEngine` inyectado.
  `run(topic: str, *, max_tokens=1024) -> Story`. Delega directamente en
  `build_story()` — envoltorio delgado de un solo Engine, mismo patrón
  que ADR-0010 ya estableció para `NarrationService` antes de que
  existiera ningún Engine: desbloquea la capa superior (`velora.cli`)
  antes de que su comportamiento distintivo completo (orquestar varios
  Engines) tenga un segundo Engine real que coordinar. Reutiliza `Story`
  como tipo de resultado — no lo envuelve en un `WorkflowResult` nuevo.
  Sin jerarquía de error propia: propaga `ValueError` (de `StoryEngine`)
  y `VeloraProviderError` (del Provider subyacente) tal cual.

`velora.workflows` (raíz) no contiene nada todavía — mismo motivo que
`velora.engines` (raíz).

### `velora.cli`: `velora create story`

Primer subcomando real de la CLI, más allá del smoke-run de Runtime
(ADR-0012). Construye la cadena completa —
`AnthropicTextGenerationProvider` → `NarrationService` → `StoryEngine` →
`StoryWorkflow` — en el composition root, con el Provider como el único
`LifecycleComponent` de un `Runtime` propio (distinto del que usa el
smoke-run por defecto). Requiere `VELORA_ANTHROPIC_API_KEY`
(`velora.configuration`, campo opcional — se valida en el punto de uso,
no al resolver Configuration). Los imports de `anthropic`,
`NarrationService`, `StoryEngine` y `StoryWorkflow` viven dentro de las
funciones que los usan, no a nivel de módulo: importar `velora.cli` (y
ejecutar cualquier comando distinto de `create story`) nunca requiere el
extra opcional `velora[anthropic]`.

## Dependencias entre componentes

```
velora.cli  →  velora.runtime
velora.cli  →  velora.configuration
velora.cli  →  velora.logging  →  velora.runtime
velora.cli  →  velora.services
velora.cli  →  velora.workflows.story          (solo dentro de `create story`, import diferido)
velora.cli  →  velora.providers.text_generation  (solo dentro de `create story`, import diferido)
velora.providers.text_generation  →  velora.runtime   (solo para LifecycleComponent)
velora.providers.text_generation  →  velora.providers  (jerarquía de error)
velora.providers.text_generation._anthropic  →  anthropic (extra opcional)
velora.providers.voice  →  velora.runtime   (solo para LifecycleComponent)
velora.providers.voice  →  velora.providers  (jerarquía de error)
velora.providers.voice._elevenlabs  →  elevenlabs, httpx (extra opcional)
velora.services.narration  →  velora.providers.text_generation
velora.services.voice  →  velora.providers.voice
velora.engines.story  →  velora.services.narration
velora.engines.narration_audio  →  velora.services.voice
velora.engines.narration_audio  →  velora.engines.story  (solo el tipo `Story`)
velora.workflows.story  →  velora.engines.story
```

`velora.engines.story` no importa `velora.providers` ni `anthropic` en
ningún punto — solo `velora.services.narration`, respetando el diagrama
canónico de ADR-0008. `velora.engines.narration_audio` sigue la misma
regla con `velora.services.voice`, y depende de `velora.engines.story`
únicamente para el tipo `Story` que recibe como entrada, no para
ninguna lógica. `velora.workflows.story` sigue la misma regla: solo
importa `velora.engines.story`, nunca se salta una capa hacia
`velora.services.narration` o `velora.providers` directamente.
`velora.cli` construye la cadena completa, pero solo dentro de la
ejecución de `create story` — sus imports de `velora.workflows.story` y
de `velora.providers.text_generation` están diferidos dentro de las
funciones que los usan, no a nivel de módulo (ADR-0012), precisamente
para que el resto de comandos de la CLI —y el propio `import velora.cli`—
nunca dependan del extra `velora[anthropic]`. `velora.engines.
narration_audio` no tiene todavía ningún consumidor real dentro del
código base — `StoryWorkflow` no lo conoce; queda disponible como Engine
completo, a la espera de que un Workflow real lo coordine junto a
`StoryEngine` (ADR-0015).

## Lo que no existe todavía

Extensions. Tampoco existen Providers de ningún otro dominio (imagen,
video, música, traducción), más Services de capacidad (`ImageService`,
etc.), más Engines (Subtitle, Timeline, Render, Publish — ver
`docs/VISION.md`), ni más Workflows que `StoryWorkflow`. Ningún Workflow
consume todavía `velora.engines.narration_audio`. Cualquier mención a
esas capas en otros documentos es planificación, no arquitectura
vigente. Este documento se actualizará en cada PR que introduzca una
capa o dominio nuevo.
