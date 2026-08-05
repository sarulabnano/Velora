# PROJECT_CONTEXT

Este documento resume el estado actual de Velora. No duplica los ADR ni
`docs/VISION.md`; los referencia.

## Último PR

**PR-011 — Services: VoiceService.**

## Milestone activa

**Services** (segundo Service de capacidad completado: `VoiceService`,
sobre `VoiceProvider`). Próxima: por decidir contigo — ver "Próximo
paso".

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
- `velora.cli` — sin cambios en este PR.
- `velora.runtime` — sin cambios funcionales en este PR.
- `velora.configuration` — sin cambios en este PR.
- `velora.logging` — sin cambios funcionales en este PR.
- `velora.services` (raíz) — Services de infraestructura, sin cambios.
- `velora.services.narration` — `NarrationService`, sin cambios.
- `velora.services.voice` — **nuevo**: `VoiceService`
  (`speak(text: str) -> SpeechResult`). Envuelve un `VoiceProvider`
  inyectado; delega directamente, reutiliza `SpeechResult` como
  resultado. Sin consumidor todavía dentro del código base.
- `velora.providers` (raíz), `velora.providers.text_generation`,
  `velora.providers.voice` — sin cambios.
- `velora.engines.story` — sin cambios.
- `velora.workflows.story` — sin cambios.

Ver `docs/architecture.md` para el detalle de cada símbolo.

## Componentes que NO existen todavía

Extensions. Tampoco Providers de imagen, video, música o traducción,
más Services de capacidad (`ImageService`, etc.), más Engines (Subtitle,
Timeline, Render, Publish), ni más Workflows que `StoryWorkflow`. Ningún
Engine/Workflow consume todavía `velora.services.voice`.

## Decisiones vigentes (ADR)

- **ADR-0001** a **ADR-0013** — ver PRs anteriores; sin cambios.
- **ADR-0014** — `VoiceService` es el mismo patrón exacto que ADR-0010
  ya estableció para `NarrationService`: contrato delgado
  (`speak(text) -> SpeechResult`), sin decidir qué voz usar (vive en el
  Provider inyectado), reutiliza `SpeechResult` sin envolverlo, valida
  solo con `ValueError` (única precondición). A diferencia de
  `NarrationService`, no tiene parámetro de configuración por defecto
  en el constructor — no hay equivalente natural a `system_prompt` para
  síntesis de voz. Vinculante para todo Service de capacidad futuro:
  mismo patrón, jerarquía de error propia solo cuando haya más de una
  condición de fallo real que lo justifique.

## Criterios de aceptación vigentes

Desde un repositorio limpio:

```
git clone <repo>
uv sync
uv run velora
uv run pytest
```

Sin cambios respecto a PR-010. El Core mantiene cobertura de pruebas
≥90%; PR-011 cierra con 100%. `velora.services.voice` no tiene
consumidor en la CLI todavía — no hay comando `velora create ...` nuevo
en este PR.

## Próximo paso

Con `NarrationService` y `VoiceService` ya existiendo — dos capacidades
genuinamente distintas — hay varios caminos razonables. A diferencia de
tras PR-009, ahora sí hay contenido real para que `StoryWorkflow`
coordine más de un paso. Necesito tu decisión antes de `Genera PR-012`:

1. **Extender `StoryWorkflow`** para que, además de construir la
   `Story`, sintetice audio para cada escena vía `VoiceService` — la
   primera vez que un Workflow coordinaría dos capacidades reales.
   Revelaría si la forma actual de `StoryWorkflow` (un solo paso,
   delgado) sigue siendo la correcta o necesita crecer/dividirse.
2. **Un Engine dedicado** (p. ej. un `NarrationAudioEngine`, análogo a
   `StoryEngine` pero para voz) antes de tocar `StoryWorkflow` — más
   fiel al diagrama canónico (`Workflow → Engines`, no `Workflow →
   Services` directamente), pero añade una capa antes de saber si hace
   falta.
3. **Tercer dominio de Provider/Service** (imagen) — sigue ampliando
   cobertura horizontal antes de profundizar la orquestación.

Mi inclinación, si preguntas: opción 2 — `StoryWorkflow` hoy depende de
`StoryEngine`, no de `NarrationService` directamente (ADR-0012: nunca se
salta una capa); que empezara a depender también de `VoiceService`
directamente rompería esa misma disciplina que el propio `StoryWorkflow`
ya sigue. Un Engine de audio mantiene el diagrama limpio y le da a un
`StoryWorkflow` extendido (o a un Workflow nuevo) algo real que
coordinar sin violar su propia regla. Pero es tu llamada.
