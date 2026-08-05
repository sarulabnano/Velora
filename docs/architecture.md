# Arquitectura vigente

Este documento describe únicamente la arquitectura que existe hoy en el
repositorio. No describe fases futuras del roadmap; esas se documentan en
`PROJECT_CONTEXT.md` (estado), `docs/VISION.md` (visión de producto) y
los ADR (decisiones).

## Estado: Workflows — `StoryWorkflow` y `velora create story`

Fase completada: **Foundation** (PR-001), **Runtime** (PR-002),
**Configuration** (PR-003), **Logging** (PR-004), **Services —
infraestructura** (PR-005), **Providers — text_generation** (PR-006),
**Services — capacidad: NarrationService** (PR-007), **Engines —
StoryEngine** (PR-008), **Workflows — StoryWorkflow** (PR-009).
Fase siguiente: a decidir — más Workflows, más Engines, o más dominios
de Providers/Services.

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
    runtime/                   # (sin cambios funcionales en este PR)
    providers/
        __init__.py         # Jerarquía de error compartida entre dominios
        _errors.py            # VeloraProviderError y su jerarquía
        text_generation/
            __init__.py         # Superficie pública del dominio
            _types.py             # Role, Message, TextGenerationRequest/Result
            _protocol.py            # TextGenerationProvider
            _anthropic.py             # AnthropicTextGenerationProvider (real, requiere extra)
    engines/
        __init__.py         # Namespace, sin lógica compartida todavía
        story/
            __init__.py         # Superficie pública del Story Engine
            _types.py              # Scene, Story
            _engine.py               # StoryEngine
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
    test_services_*.py            # 3 archivos (incluye narration)
    test_providers_*.py           # 4 archivos
    test_engines_*.py             # 2 archivos
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
velora.services.narration  →  velora.providers.text_generation
velora.engines.story  →  velora.services.narration
velora.workflows.story  →  velora.engines.story
```

`velora.engines.story` no importa `velora.providers` ni `anthropic` en
ningún punto — solo `velora.services.narration`, respetando el diagrama
canónico de ADR-0008. `velora.workflows.story` sigue la misma regla: solo
importa `velora.engines.story`, nunca se salta una capa hacia
`velora.services.narration` o `velora.providers` directamente.
`velora.cli` construye la cadena completa, pero solo dentro de la
ejecución de `create story` — sus imports de `velora.workflows.story` y
de `velora.providers.text_generation` están diferidos dentro de las
funciones que los usan, no a nivel de módulo (ADR-0012), precisamente
para que el resto de comandos de la CLI —y el propio `import velora.cli`—
nunca dependan del extra `velora[anthropic]`.

## Lo que no existe todavía

Extensions. Tampoco existen Providers de ningún otro dominio (voz,
imagen, video, música, traducción), más Services de capacidad
(`ImageService`, etc.), más Engines (Subtitle, Timeline, Render, Publish
— ver `docs/VISION.md`), ni más Workflows que `StoryWorkflow`. Cualquier
mención a esas capas en otros documentos es planificación, no
arquitectura vigente. Este documento se actualizará en cada PR que
introduzca una capa o dominio nuevo.
