# PROJECT_CONTEXT

Este documento resume el estado actual de Velora. No duplica los ADR; los
referencia.

## Último PR

**PR-003 — Configuration.**

## Milestone activa

**Configuration** (completada). Próxima: **Logging** (PR-004).

## Roadmap (congelado, no modificable)

```
Foundation → Runtime → Configuration → Logging → Services →
Providers → Engines → Workflows → Extensions
```

## Componentes que existen hoy

- `velora` — paquete raíz, expone `__version__`.
- `velora.cli` — entrypoint de consola `velora`, composition root; por
  defecto resuelve `Configuration`, bootstrapea el Runtime y reporta su
  `runtime_id` y el `environment` resuelto.
- `velora.runtime` — núcleo estable: `Runtime`, `RuntimeState`,
  `RuntimeContext`, `LifecycleComponent`, `RuntimeEvent`,
  `RuntimeEventKind`, `RuntimeEventListener`, `VeloraRuntimeError` y su
  jerarquía.
- `velora.configuration` — único punto de entrada de configuración
  tipada: `load_settings`, `VeloraSettings`, `Environment`,
  `ConfigSource`, `EnvironmentSource`, `VeloraConfigurationError` y su
  jerarquía. No depende de `velora.runtime`.

Ver `docs/architecture.md` para el detalle de cada símbolo.

## Componentes que NO existen todavía

Logging, Services, Providers, Engines, Workflows, Extensions.

## Decisiones vigentes (ADR)

- **ADR-0001** — `Configuration` no depende de `Logging` en tiempo de
  import; produce errores tipados, nunca logging directo. Refinada por
  ADR-0005 en cuanto a qué módulo concreto conecta los errores.
- **ADR-0002** — El entrypoint CLI es funcionalidad real y permanente,
  extendido en cada fase, nunca reemplazado.
- **ADR-0003** — Máquina de estados del Runtime, instancia de un solo
  uso, arranque fail-fast-con-unwind, parada exhaustiva. Vinculante para
  todo `LifecycleComponent`.
- **ADR-0004** — `RuntimeEvent` como dataclass plano + enum. Excepciones
  de listeners no se capturan.
- **ADR-0005** — Refina ADR-0001: la "Runtime" que conecta Configuration
  y Logging es la capa/composition root (`velora.cli.main`), no la clase
  `Runtime`. `Configuration` no implementa `LifecycleComponent` — no es
  un recurso con arranque/parada. Se resuelve una sola vez, antes de
  construir el `Runtime`. Vinculante para PR-004 (Logging): su
  construcción e inyección como `RuntimeEventListener` ocurre en
  `velora.cli.main`.

## Criterios de aceptación vigentes

Desde un repositorio limpio:

```
git clone <repo>
uv sync
uv run velora
uv run pytest
```

Todo debe ejecutarse sin errores. `pytest` debe invocarse a través del
entorno gestionado por `uv` (`uv run pytest`, o con `.venv` activado);
un `pytest` resuelto fuera de ese entorno no tendrá instalado
`pytest-cov` y fallará por flags de cobertura no reconocidos. El Core
(actualmente: `velora`, `velora.cli`, `velora.runtime`,
`velora.configuration`) mantiene cobertura de pruebas ≥90% como gate de
aceptación, no como meta aspiracional; PR-003 cierra con 100%.

`os.environ` solo puede leerse en
`src/velora/configuration/_sources.py`; esto es una invariante
verificada por `tests/test_no_direct_environ_access.py`, no solo una
convención documentada.

## Próximo paso

**PR-004 — Logging.** Debe implementar un backend de logging real que
consuma `RuntimeEventListener` (ADR-0004) sin que `Runtime` conozca su
implementación concreta, y sin importar `velora.configuration`
directamente — su configuración (nivel, formato, destino) se resuelve en
el composition root a partir de `VeloraSettings` (o una extensión suya)
y se le inyecta ya tipada al construirse (ADR-0005). Su
`on_runtime_event` debe ser, en la práctica, total: no debe existir un
`RuntimeEventKind` para el cual pueda lanzar una excepción (ADR-0004).
