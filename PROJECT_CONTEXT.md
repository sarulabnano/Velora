# PROJECT_CONTEXT

Este documento resume el estado actual de Velora. No duplica los ADR; los
referencia.

## Último PR

**PR-002 — Runtime Core.**

## Milestone activa

**Runtime** (completada). Próxima: **Configuration** (PR-003).

## Roadmap (congelado, no modificable)

```
Foundation → Runtime → Configuration → Logging → Services →
Providers → Engines → Workflows → Extensions
```

## Componentes que existen hoy

- `velora` — paquete raíz, expone `__version__`.
- `velora.cli` — entrypoint de consola `velora`, soporta `--version` y
  `--help`; por defecto bootstrapea el Runtime y reporta su `runtime_id`.
- `velora.runtime` — núcleo estable: `Runtime`, `RuntimeState`,
  `RuntimeContext`, `LifecycleComponent`, `RuntimeEvent`,
  `RuntimeEventKind`, `RuntimeEventListener`, `VeloraRuntimeError` y su
  jerarquía. Ver `docs/architecture.md` para el detalle de cada símbolo.

## Componentes que NO existen todavía

Configuration, Logging, Services, Providers, Engines, Workflows,
Extensions.

## Decisiones vigentes (ADR)

- **ADR-0001** — `Configuration` no depende de `Logging` en tiempo de
  import. `Runtime` es el único componente que conoce a ambos y conecta
  los errores tipados de `Configuration` con `Logging` durante el
  bootstrap. Vinculante para el diseño de PR-003 (Configuration) y PR-004
  (Logging).
- **ADR-0002** — El entrypoint CLI de Foundation (`velora.cli`) es
  funcionalidad real y permanente, no un stub del Runtime. Cada fase debe
  extenderlo, nunca reemplazarlo; PR-002 lo extendió para bootstrapear el
  Runtime por defecto, preservando `--version`/`--help` intactos.
- **ADR-0003** — Máquina de estados del Runtime (`NOT_STARTED →
  STARTING → RUNNING → STOPPING → STOPPED`, con `FAILED` como terminal de
  error), instancia de un solo uso (sin reinicio), arranque
  fail-fast-con-unwind, parada exhaustiva (best-effort en todos los
  componentes aunque uno falle). Vinculante para todo componente que
  implemente `LifecycleComponent` en fases futuras.
- **ADR-0004** — Modelo de eventos del Runtime: `RuntimeEvent` es un
  dataclass plano con un campo `kind: RuntimeEventKind`, no una jerarquía
  de clases (estabilidad frente a nuevos tipos de evento). Las
  excepciones de listeners no se capturan: interrumpen el Runtime de
  inmediato. Vinculante para el diseño de Logging (PR-004): su
  `on_runtime_event` debe ser, en la práctica, total.

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
(actualmente: `velora`, `velora.cli`, `velora.runtime`) mantiene
cobertura de pruebas ≥90% como gate de aceptación, no como meta
aspiracional; PR-002 cierra con 100%.

## Próximo paso

**PR-003 — Configuration.** Debe implementar la resolución de
configuración completamente tipada, sin accesos directos a `os.environ`
fuera del propio módulo, y sin importar `velora.runtime` en tiempo de
import salvo por el protocolo `LifecycleComponent` que deberá
implementar para participar del ciclo de vida (ver ADR-0001 y ADR-0003).
Los errores de configuración deben representarse como excepciones
tipadas propias del módulo — nunca logging directo — para que `Runtime`
pueda conectarlos con `Logging` durante el bootstrap una vez esa fase
exista (ADR-0001).
