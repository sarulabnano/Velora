# ADR-0002: El entrypoint CLI de Foundation es funcionalidad real, no un stub

## Status

Accepted

## Context

El criterio de aceptación de PR-001 exige que, desde un repositorio
limpio, `uv run velora` se ejecute sin errores. Sin embargo, el `Runtime`
(bootstrap, lifecycle, contexto de ejecución) no se construye hasta
PR-002. El manifiesto de ingeniería prohíbe explícitamente placeholders,
código temporal, comentarios `TODO` y el uso de `pass` como cuerpo de
función.

Existe una tensión aparente: ¿cómo puede `velora` ejecutarse si el
Runtime todavía no existe, sin recurrir a un stub desechable?

## Decision

El entrypoint `velora` de PR-001 no simula al Runtime: expone
funcionalidad de CLI legítima y permanente que cualquier herramienta
madura necesita — `velora --version` y `velora --help` — implementada
mediante `argparse` y `importlib.metadata`, sin ninguna dependencia del
Runtime.

Esta decisión implica:

1. El módulo `velora.cli` es parte de la API pública mínima del proyecto
   desde PR-001, no un artefacto temporal.
2. Cuando `Runtime` exista (PR-002), `velora.cli.main` se extenderá para
   invocarlo como comportamiento por defecto (sin flags), preservando
   `--version` y `--help` tal cual. No se reescribe ni se descarta.
3. La versión reportada por el CLI tiene una única fuente de verdad: el
   campo `version` de `pyproject.toml`, leído en tiempo de ejecución vía
   `importlib.metadata`. Nunca se duplica como literal en el código
   fuente.

## Consequences

- PR-001 cumple el criterio de aceptación (`uv run velora` funciona) sin
  introducir deuda técnica ni funcionalidad desechable.
- El módulo `cli.py` queda bajo el mismo estándar de calidad y cobertura
  que el resto del Core, ya que no es temporal.
- PR-002 tiene una restricción adicional autoimpuesta: extender
  `cli.main`, no reemplazarlo.
