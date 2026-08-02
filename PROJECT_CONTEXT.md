# PROJECT_CONTEXT

Este documento resume el estado actual de Velora. No duplica los ADR; los
referencia.

## Último PR

**PR-004 — Logging.**

## Milestone activa

**Logging** (completada). Próxima: **Services** (PR-005).

## Roadmap (congelado, no modificable)

```
Foundation → Runtime → Configuration → Logging → Services →
Providers → Engines → Workflows → Extensions
```

## Componentes que existen hoy

- `velora` — paquete raíz, expone `__version__`.
- `velora.cli` — entrypoint de consola `velora`, composition root; por
  defecto resuelve `Configuration`, configura `Logging` a partir de ella,
  bootstrapea el Runtime con el logger como listener, y reporta
  `runtime_id` y `environment`.
- `velora.runtime` — núcleo estable: `Runtime`, `RuntimeState`,
  `RuntimeContext`, `LifecycleComponent`, `RuntimeEvent`,
  `RuntimeEventKind`, `RuntimeEventListener`, `VeloraRuntimeError` y su
  jerarquía.
- `velora.configuration` — único punto de entrada de configuración
  tipada: `load_settings`, `VeloraSettings`, `Environment`, `LogLevel`,
  `ConfigSource`, `EnvironmentSource`, `VeloraConfigurationError` y su
  jerarquía. No depende de `velora.runtime` ni de `velora.logging`.
- `velora.logging` — backend de logging real: `configure_logging`,
  `RuntimeEventLogger` (implementa `RuntimeEventListener`),
  `LoggingSettings`, `LogLevel` (propio, distinto del de Configuration —
  ADR-0006). No depende de `velora.configuration`.

Ver `docs/architecture.md` para el detalle de cada símbolo.

## Componentes que NO existen todavía

Services, Providers, Engines, Workflows, Extensions.

## Decisiones vigentes (ADR)

- **ADR-0001** — `Configuration` no depende de `Logging` en tiempo de
  import; produce errores tipados, nunca logging directo. Refinada por
  ADR-0005.
- **ADR-0002** — El entrypoint CLI es funcionalidad real y permanente,
  extendido en cada fase, nunca reemplazado.
- **ADR-0003** — Máquina de estados del Runtime, instancia de un solo
  uso, arranque fail-fast-con-unwind, parada exhaustiva.
- **ADR-0004** — `RuntimeEvent` como dataclass plano + enum. Excepciones
  de listeners no se capturan. `RuntimeEventLogger` (Logging) cumple
  "en la práctica total" vía `match` exhaustivo + `assert_never`.
- **ADR-0005** — La "Runtime" que conecta Configuration y Logging es el
  composition root (`velora.cli.main`), no la clase `Runtime`.
  `Configuration` no implementa `LifecycleComponent`.
- **ADR-0006** — `LogLevel` existe por duplicado, independiente, en
  `velora.configuration` y `velora.logging` — ninguno importa al otro
  (Logging no puede depender de Configuration por dirección de capas;
  Configuration no puede depender de Logging por ADR-0001). El
  composition root traduce entre ambos por nombre de miembro. Vinculante
  para cualquier tipo futuro que dos capas no adyacentes-por-import
  necesiten compartir.

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
`velora.configuration`, `velora.logging`) mantiene cobertura de pruebas
≥90% como gate de aceptación, no como meta aspiracional; PR-004 cierra
con 100%.

`os.environ` solo puede leerse en
`src/velora/configuration/_sources.py`; verificado por
`tests/test_no_direct_environ_access.py`, no solo documentado.

`VELORA_LOG_LEVEL` controla la verbosidad del logging real
(`DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`, por defecto `INFO`); los
eventos del Runtime se registran en `stderr`.

## Próximo paso

**PR-005 — Services.** Es la primera fase que se sitúa por encima de
`Configuration` en el diagrama de capas
(`Providers → Services → Configuration → Logging → Runtime`), así que
puede depender de `Configuration` libremente (dirección permitida). Debe
decidir explícitamente si un Service es o no un `LifecycleComponent`
(muchos Services sí tendrán recursos reales que abrir/cerrar — conexiones
a bases de datos, colas, clientes HTTP persistentes — a diferencia de
Configuration y Logging, que no los tenían). El cableado de cualquier
Service concreto en el composition root sigue el mismo patrón que
Configuration y Logging: construido explícitamente en `velora.cli.main`,
nunca instanciado dentro de `Runtime`.
