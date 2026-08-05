# PROJECT_CONTEXT

Este documento resume el estado actual de Velora. No duplica los ADR ni
`docs/VISION.md`; los referencia.

## Último PR

**PR-008 — Engines: StoryEngine.**

## Milestone activa

**Engines** (primer Engine completado: `StoryEngine`, sobre
`NarrationService`). Próxima: por decidir contigo — ver "Próximo paso".

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
- `velora.services` (raíz) — Services de infraestructura, sin cambios.
- `velora.services.narration` — `NarrationService`, sin cambios.
- `velora.providers`, `velora.providers.text_generation` — sin cambios.
- `velora.engines.story` — **nuevo**: `Scene`, `Story` (tipos),
  `StoryEngine` (`build_story(topic, *, max_tokens=1024) -> Story`).
  Genera narración vía `NarrationService` inyectado y la divide en
  escenas por párrafos.

Ver `docs/architecture.md` para el detalle de cada símbolo.

## Componentes que NO existen todavía

Workflows, Extensions. Tampoco Providers de voz, imagen, video, música o
traducción, más Services de capacidad, ni más Engines (Subtitle,
Timeline, Render, Publish).

## Decisiones vigentes (ADR)

- **ADR-0001** a **ADR-0010** — ver PRs anteriores; sin cambios.
- **ADR-0011** — `StoryEngine` divide escenas por párrafos (determinista,
  no depende de que el modelo siga un delimitador pedido); sin control
  de `scene_count` (fuera de alcance deliberado); historia vacía es
  estado válido, no error; `ValueError` para la única precondición, sin
  jerarquía de error de `velora.engines` todavía. Vinculante para todo
  Engine futuro: criterio propio de división si aplica, sin extraer
  utilidad compartida hasta que un segundo consumidor real la necesite.

## Criterios de aceptación vigentes

Desde un repositorio limpio:

```
git clone <repo>
uv sync
uv run velora
uv run pytest
```

Sin cambios respecto a PR-007. El Core mantiene cobertura de pruebas
≥90%; PR-008 cierra con 100%.

## Próximo paso

Con `StoryEngine` funcionando, hay varios caminos razonables — necesito
tu decisión antes de `Genera PR-009`, igual que en PR-008:

1. **Más Engines** (Subtitle Engine, Timeline Engine...) antes de
   Workflows — sigue completando la capa antes de orquestarla.
2. **PR-009 — Workflows**: el primer Workflow real, orquestando
   `StoryEngine` (y, a futuro, más Engines) en un pipeline completo — el
   primer punto donde `velora.cli` tendría un consumidor real que
   invocar, más allá del smoke-run actual de Runtime.
3. **Segundo dominio de Providers/Service de capacidad** (voz, imagen)
   si prefieres ampliar cobertura horizontal antes de subir de capa.

Mi inclinación, si preguntas: opción 2 (Workflows) — un solo Engine ya
es suficiente para demostrar un Workflow real de principio a fin, y eso
por fin le da a `velora.cli` algo que hacer más allá de arrancar y
apagar el Runtime. Pero es tu llamada.
