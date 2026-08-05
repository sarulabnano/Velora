# Velora

Velora es una plataforma pensada para evolucionar durante al menos diez
años sin que su Runtime necesite reescribirse. Prioriza estabilidad,
mantenibilidad y extensibilidad por encima de velocidad de desarrollo
inicial.

## Estado actual

**Fase: Workflows — `StoryWorkflow`** (PR-009). Ver
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

## Services de capacidad

`NarrationService` es la primera capacidad construida sobre un
Provider — el llamador nunca sabe cuál (`docs/VISION.md`):

```python
from velora.services.narration import NarrationService

service = NarrationService(provider)  # cualquier TextGenerationProvider
result = service.narrate("Describe a city at dawn, in two sentences.")
print(result.text)
```

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

## Workflows

`StoryWorkflow` es el primer Workflow: envuelve un `StoryEngine`
inyectado y ejecuta el pipeline completo (`docs/VISION.md`: "Los
Workflows conectan todos los motores"):

```python
from velora.workflows.story import StoryWorkflow

workflow = StoryWorkflow(engine)  # el mismo StoryEngine de arriba
story = workflow.run("The history of the printing press")
```

También es el primer subcomando real de la CLI, más allá del smoke-run
de Runtime:

```bash
VELORA_ANTHROPIC_API_KEY=sk-ant-... uv run velora create story \
    --topic "The history of the printing press"
```

```
Story: The history of the printing press (3 scene(s))

[0] ...
[1] ...
[2] ...
```

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
