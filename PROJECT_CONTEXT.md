# PROJECT_CONTEXT

Este documento resume el estado actual de Velora. No duplica los ADR; los
referencia.

## Último PR

**PR-001 — Repository Foundation.**

## Milestone activa

**Foundation** (completada). Próxima: **Runtime** (PR-002).

## Roadmap (congelado, no modificable)

```
Foundation → Runtime → Configuration → Logging → Services →
Providers → Engines → Workflows → Extensions
```

## Componentes que existen hoy

- `velora` — paquete raíz, expone `__version__`.
- `velora.cli` — entrypoint de consola `velora`, soporta `--version` y
  `--help`.

## Componentes que NO existen todavía

Runtime, Configuration, Logging, Services, Providers, Engines, Workflows,
Extensions.

## Decisiones vigentes (ADR)

- **ADR-0001** — `Configuration` no depende de `Logging` en tiempo de
  import. `Runtime` es el único componente que conoce a ambos y conecta
  los errores tipados de `Configuration` con `Logging` durante el
  bootstrap. Vinculante para el diseño de PR-003 (Configuration) y PR-004
  (Logging).
- **ADR-0002** — El entrypoint CLI de Foundation (`velora.cli`) es
  funcionalidad real y permanente, no un stub del Runtime. PR-002 debe
  extenderlo, nunca reemplazarlo.

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
`pytest-cov` y fallará por flags de cobertura no reconocidos. El Core (actualmente: `velora`,
`velora.cli`) mantiene cobertura de pruebas ≥90% como gate de aceptación,
no como meta aspiracional.

## Próximo paso

**PR-002 — Runtime Core.** Debe definir: bootstrap, lifecycle, contexto
de ejecución, apagado ordenado, manejo de errores fatales, y el mecanismo
de emisión de eventos que permitirá a `Logging` (fase posterior)
suscribirse sin que `Runtime` conozca implementaciones concretas de
logging (ver `architecture.md` §7 en el documento de arquitectura
objetivo). Debe extender `velora.cli.main`, no reemplazarlo (ADR-0002).
