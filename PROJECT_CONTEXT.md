# PROJECT_CONTEXT

Este documento resume el estado actual de Velora. No duplica los ADR ni
`docs/VISION.md`; los referencia.

## Último PR

**PR-007 — Services (capacidad): NarrationService.**

## Milestone activa

**Services de capacidad** (primer Service completado: `NarrationService`,
sobre `TextGenerationProvider`/Anthropic). Próxima: **Engines** — pero
requiere decidir explícitamente qué Engine construir primero (ver
"Próximo paso").

## Roadmap (congelado, no modificable)

```
Foundation → Runtime → Configuration → Logging → Services →
Providers → Engines → Workflows → Extensions
```

## Documento de visión

`docs/VISION.md` — visión de producto. Incorporado en PR-005.
Discrepancias con lo construido se resuelven vía ADR.

## Componentes que existen hoy

- `velora` — paquete raíz, expone `__version__`.
- `velora.cli` — composition root: Configuration → Logging → Runtime
  (con Services de infraestructura inyectado). Sin cambios en este PR.
- `velora.runtime`, `velora.configuration`, `velora.logging` — sin
  cambios funcionales en este PR.
- `velora.services` (raíz) — Services de infraestructura (`Clock`,
  `IdGenerator`), sin cambios en este PR.
- `velora.providers`, `velora.providers.text_generation` — sin cambios
  en este PR.
- `velora.services.narration` — **nuevo**: `NarrationService`, primer
  Service de capacidad. Envuelve `TextGenerationProvider` inyectado;
  `narrate(instructions, *, max_tokens=1024) -> TextGenerationResult`.

Ver `docs/architecture.md` para el detalle de cada símbolo.

## Componentes que NO existen todavía

Engines, Workflows, Extensions. Tampoco Providers de voz, imagen, video,
música o traducción, ni más Services de capacidad (`ImageService`, etc.).

## Decisiones vigentes (ADR)

- **ADR-0001** a **ADR-0009** — ver PRs anteriores; sin cambios.
- **ADR-0010** — `NarrationService` se construye antes de Engines (para
  que Engines pueda depender de un Service, nunca de un Provider
  directamente, per el diagrama canónico de ADR-0008). Contrato
  deliberadamente delgado: no decide estructura narrativa. Reutiliza
  `TextGenerationResult` en vez de un tipo nuevo. Validación mínima con
  `ValueError` estándar, sin jerarquía de error propia todavía.
  Vinculante para todo Service de capacidad futuro (`ImageService`,
  etc.): mismo patrón — subpaquete de `velora.services`, contrato
  delgado, reutilizar tipos de resultado del dominio de Provider,
  jerarquía de error propia solo si hay más de una condición de fallo
  real.

## Criterios de aceptación vigentes

Desde un repositorio limpio:

```
git clone <repo>
uv sync
uv run velora
uv run pytest
```

Sin cambios respecto a PR-006. El Core (`velora`, `velora.cli`,
`velora.runtime`, `velora.configuration`, `velora.logging`,
`velora.services`, `velora.providers`) mantiene cobertura de pruebas
≥90%; PR-007 cierra con 100%.

## Próximo paso

**Engines** es, de los conceptos del roadmap, el menos especificado
todavía: ni AGENT.md, ni `architecture.md` original, ni `docs/VISION.md`
dan más que un párrafo y una lista de ejemplos (Story Engine, Subtitle
Engine, Timeline Engine, Render Engine, Publish Engine). Antes de
`Genera PR-008`, hace falta decidir contigo, explícitamente, cuál
Engine construir primero — no debería decidirlo yo solo sin más
contexto de producto, a diferencia de las decisiones de PR-005 a PR-007,
que sí tenían suficiente información en VISION.md para justificarse por
sí solas. Candidatos razonables dado lo ya construido:

1. **Story Engine mínimo** — el más natural, dado que ya existe
   `NarrationService` para respaldarlo; probablemente el primer Engine
   que `docs/VISION.md` esperaría ver.
2. Exponer `NarrationService` directamente a través de un Workflow
   trivial de un solo paso, aplazando "lógica compleja" real hasta tener
   más de un Engine con el que orquestar.
