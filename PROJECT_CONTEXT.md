# PROJECT_CONTEXT

Este documento resume el estado actual de Velora. No duplica los ADR ni
`docs/VISION.md`; los referencia.

## Último PR

**PR-009 — Workflows: StoryWorkflow + `velora create story`.**

## Milestone activa

**Workflows** (primer Workflow completado: `StoryWorkflow`, sobre
`StoryEngine`). Próxima: por decidir contigo — ver "Próximo paso".

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
  (con Services de infraestructura inyectado). **Nuevo en este PR**:
  primer subcomando real, `velora create story --topic TOPIC
  [--max-tokens N]`, que ejecuta `StoryWorkflow` de principio a fin.
  Requiere `VELORA_ANTHROPIC_API_KEY`. El smoke-run por defecto,
  `--version` y `--help` no cambian.
- `velora.runtime` — sin cambios funcionales en este PR.
- `velora.configuration` — **nuevo en este PR**: `VeloraSettings` gana
  `anthropic_api_key: str | None` (de `VELORA_ANTHROPIC_API_KEY`),
  opcional, sin validar en `from_source()` — se valida en el punto de
  uso (`velora create story`).
- `velora.logging` — sin cambios funcionales en este PR.
- `velora.services` (raíz) — Services de infraestructura, sin cambios.
- `velora.services.narration` — `NarrationService`, sin cambios.
- `velora.providers`, `velora.providers.text_generation` — sin cambios.
- `velora.engines.story` — sin cambios.
- `velora.workflows.story` — **nuevo**: `StoryWorkflow`
  (`run(topic, *, max_tokens=1024) -> Story`). Envuelve un `StoryEngine`
  inyectado; delega directamente, reutiliza `Story` como resultado.

Ver `docs/architecture.md` para el detalle de cada símbolo.

## Componentes que NO existen todavía

Extensions. Tampoco Providers de voz, imagen, video, música o
traducción, más Services de capacidad, más Engines (Subtitle, Timeline,
Render, Publish), ni más Workflows que `StoryWorkflow`.

## Decisiones vigentes (ADR)

- **ADR-0001** a **ADR-0011** — ver PRs anteriores; sin cambios.
- **ADR-0012** — `StoryWorkflow` es un envoltorio delgado de un solo
  Engine, mismo patrón que ADR-0010 aplicó a `NarrationService`: se
  construye ahora para desbloquear `velora.cli`, antes de que exista un
  segundo Engine que coordinar. `velora create story` construye toda la
  cadena (Provider → NarrationService → StoryEngine → StoryWorkflow) en
  el composition root; el Provider es el único `LifecycleComponent` de
  un `Runtime` propio, separado del que usa el smoke-run por defecto —
  `runtime_factory` no se toca. Los imports de `anthropic`,
  `NarrationService`, `StoryEngine` y `StoryWorkflow` están diferidos
  dentro de las funciones que los usan: importar `velora.cli`, o correr
  cualquier comando distinto de `create story`, nunca requiere el extra
  `velora[anthropic]`. Vinculante para todo Workflow futuro: subpaquete
  propio de `velora.workflows`, Engine(s) inyectados, subcomando aditivo
  bajo `create`.

## Criterios de aceptación vigentes

Desde un repositorio limpio:

```
git clone <repo>
uv sync
uv run velora
uv run pytest
```

Sin cambios respecto a PR-008. El Core mantiene cobertura de pruebas
≥90%; PR-009 cierra con 100%. `uv run velora create story --topic "..."`
requiere además `VELORA_ANTHROPIC_API_KEY` en el entorno.

## Próximo paso

Con `StoryWorkflow` funcionando y `velora create story` operativo de
principio a fin, hay varios caminos razonables — necesito tu decisión
antes de `Genera PR-010`:

1. **Segundo dominio de Providers/Service de capacidad** (voz o imagen)
   — amplía cobertura horizontal; no añade un segundo Engine todavía.
2. **Un segundo Engine** (Subtitle Engine, sobre el primer dominio de
   voz que exista) — la primera vez que `StoryWorkflow` tendría más de
   un Engine real que coordinar, revelando si su forma actual (delgada,
   de un solo paso) sigue siendo la correcta o necesita crecer.
3. **Un segundo Workflow** sobre lo que ya existe — más difícil de
   justificar todavía: no hay un segundo Engine real que un segundo
   Workflow pudiera componer de forma distinta a `StoryWorkflow`.

Mi inclinación, si preguntas: opción 1 (voz o imagen) — es la que más
directamente desbloquea un segundo Engine real después, y evita
construir un segundo Workflow o un segundo Engine antes de tener con qué
llenarlo de contenido genuinamente distinto. Pero es tu llamada.
