# ADR-0012: `StoryWorkflow` y `velora create story` — el primer Workflow real

## Status

Accepted

## Context

Tras PR-008 (`StoryEngine`), `PROJECT_CONTEXT.md` dejaba tres caminos
igualmente razonables para PR-009: más Engines, un segundo dominio de
Providers/Services, o Workflows. Se eligió Workflows: un solo Engine ya
es suficiente para demostrar un pipeline real de principio a fin, y es
el primer punto donde `velora.cli` tiene un consumidor real que invocar
más allá del smoke-run de Runtime (`architecture.md`: "`velora.cli`
todavía no construye ni usa `StoryEngine`: no hay Workflow que lo
necesite todavía").

`docs/VISION.md` describe Workflows como la capa que "conecta todos los
motores" y lista ejemplos de CLI orientados a entregables terminados
(`velora create documentary`, `velora create short`, `velora create
podcast`). Ninguno de esos entregables es construible hoy: todos
requieren Engines (imagen, video, audio, render, publish) que no
existen. Solo existe un Engine, `StoryEngine`, que produce una narración
dividida en escenas — no un producto audiovisual terminado.

## Decision

### `velora.workflows.story.StoryWorkflow`: envoltorio delgado de un solo Engine

Mismo patrón exacto que ADR-0010 estableció para `NarrationService`
antes de que existiera ningún Engine: construir una capa delgada que
desbloquea la capa superior (`velora.cli`) antes de que su
comportamiento distintivo completo (orquestar *varios* Engines en un
pipeline) tenga un segundo Engine real que coordinar. `StoryWorkflow`
envuelve un `StoryEngine` inyectado; `run(topic, *, max_tokens=1024) ->
Story` delega directamente en `build_story()`. Reutiliza `Story` como
tipo de resultado — no lo envuelve en un `WorkflowResult` nuevo — por la
misma razón que ADR-0010 ya aplicó a `TextGenerationResult`: `Story` ya
es agnóstico de Workflow, envolverlo de nuevo añadiría ceremonia, no
independencia.

Vive en su propio subpaquete (`velora.workflows.story`), no en la raíz
de `velora.workflows` — mismo patrón que `velora.engines.story` y
`velora.providers.text_generation`. La raíz de `velora.workflows` queda
vacía: ningún segundo Workflow ha revelado todavía una necesidad
compartida real (Regla de oro, ya aplicada en ADR-0008 y ADR-0011 a
`providers`/`engines`).

`StoryWorkflow` depende de `velora.engines.story`, nunca de
`velora.services.narration` ni de `velora.providers` directamente — no
se salta una capa del diagrama canónico de ADR-0008. Sin jerarquía de
error propia: propaga `ValueError` (precondición de `StoryEngine`) y
`VeloraProviderError` (del Provider subyacente) tal cual, mismo patrón
que ADR-0010/ADR-0011 ya establecieron para `NarrationService` y
`StoryEngine`.

### Naming del comando: `story`, no un entregable de `docs/VISION.md`

`velora create story` en vez de `velora create documentary`/`short`/
`podcast`. Nombrar el comando como un entregable terminado que todavía
no se puede producir sería falsear lo que la herramienta realmente hace
hoy. `story` nombra con precisión el resultado real: una narración
dividida en escenas. Los entregables de `docs/VISION.md` se añaden como
subcomandos adicionales de `create`, aditivos, cuando sus Engines
existan — nada en esta decisión los excluye.

### CLI: extensión aditiva, no reescritura (ADR-0002)

`_build_parser()` gana subparsers (`create story --topic TOPIC
[--max-tokens N]`), pero el comportamiento sin argumentos (smoke-run de
Runtime) y `--version`/`--help` quedan exactamente igual — ningún test
existente de esos caminos cambia. `main()` gana dos parámetros nuevos,
inyectables como los ya existentes (`provider_factory`,
`workflow_runtime_factory`), pero `runtime_factory` —el ya existente,
usado por el smoke-run— no se toca: se construye un `Runtime` *distinto*
para `create story` (con el Provider como su único
`LifecycleComponent`), en vez de generalizar `runtime_factory` para
aceptar `components` y arriesgar romper su contrato de un solo argumento
ya cubierto por tests existentes.

### `VELORA_ANTHROPIC_API_KEY`: opcional en `VeloraSettings`, validado en el punto de uso

`VeloraSettings` gana `anthropic_api_key: str | None = None`. No se
valida su presencia en `from_source()` (a diferencia de
`environment`/`log_level`, que sí tienen validación de enum): el
smoke-run por defecto de `velora` no lo necesita, así que exigirlo ahí
rompería el criterio de aceptación vigente ("desde un repositorio
limpio, `uv run velora` funciona"). `_run_create_story` lo comprueba
antes de construir nada — mismo patrón "fail fast antes de efectos
secundarios" que ya usa `VeloraConfigurationError`— y termina con el
mismo formato de mensaje (`fatal: ...` a stderr, código 1) que un fallo
de Configuration o de Runtime.

### Imports diferidos de `anthropic` dentro de `_run_create_story`

`velora.providers.text_generation.__init__` importa
`AnthropicTextGenerationProvider` de forma incondicional — importar ese
paquete sin el extra `velora[anthropic]` instalado lanza `ImportError`
(deliberado, ver `_anthropic.py`). Antes de este PR nada en el camino de
importación de `velora.cli` llegaba a tocar ese paquete en tiempo real
(solo `TYPE_CHECKING`); `create story` es el primer lugar que sí lo
necesita en tiempo de ejecución. Para no convertir `anthropic` en una
dependencia dura de `velora.cli` —y por tanto de *todo* uso de
`velora`, incluido `--version` y el smoke-run, para quien no instaló el
extra— los imports reales de `AnthropicTextGenerationProvider`,
`NarrationService`, `StoryEngine` y `StoryWorkflow` viven dentro de los
cuerpos de función que los usan (`_default_text_generation_provider_
factory`, `_run_create_story`), no a nivel de módulo. Quien ejecute
`velora create story` sin el extra instalado recibe el mismo
`ImportError` explicativo que ya emite `_anthropic.py`
("`pip install 'velora[anthropic]'`"), sin necesidad de un mensaje
duplicado en `cli.py`.

Nota fuera de alcance: `velora.services.narration` en sí ya importa
`velora.providers.text_generation` (y por tanto exige el extra) de forma
incondicional a nivel de módulo, incluso para quien nunca use Anthropic
específicamente. Es una tensión preexistente a este PR — no introducida
ni resuelta aquí — que se vuelve visible por primera vez porque
`create story` es el primer camino de ejecución real (no solo de tipos)
que llega a `NarrationService`. Corregirla (p. ej. haciendo perezosa la
importación de cada Provider concreto dentro de su dominio) es una
decisión propia, para una ADR futura si un segundo dominio de Provider
la justifica.

## Consequences

- `velora create story --topic "..."` es el primer comando real de la
  CLI más allá del smoke-run: construye la cadena completa
  (`AnthropicTextGenerationProvider` → `NarrationService` →
  `StoryEngine` → `StoryWorkflow`) en `velora.cli`, el composition root,
  igual que el resto de la cadena de Runtime/Logging — ninguna capa
  intermedia construye sus propias dependencias.
- El Provider se registra como el único `LifecycleComponent` del
  `Runtime` de este comando: `start()`/`stop()` los invoca `Runtime`,
  nunca se llaman a mano (mismo patrón que ya documenta el `README.md`
  para el uso aislado del Provider).
- Los tests de `create story` inyectan un Provider falso vía
  `provider_factory` — nunca hacen una llamada HTTP real — mismo patrón
  de frontera simulada que ya usan los tests de `StoryEngine`
  (ADR-0011).
- Cualquier Workflow futuro (`ShortWorkflow`, `DocumentaryWorkflow`, ...)
  sigue el mismo patrón: subpaquete propio de `velora.workflows`,
  Engine(s) inyectados, subcomando aditivo bajo `create`. La raíz de
  `velora.workflows` gana infraestructura compartida (p. ej. un
  contrato `Workflow` común) solo cuando un segundo Workflow revele qué
  tendría sentido compartir — no antes.
