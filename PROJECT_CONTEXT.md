# PROJECT_CONTEXT

Este documento resume el estado actual de Velora. No duplica los ADR ni
`docs/VISION.md`; los referencia.

## Último PR

**PR-012 — Engines: NarrationAudioEngine.**

## Milestone activa

**Engines** (segundo Engine completado: `NarrationAudioEngine`, sobre
`VoiceService`). Próxima: por decidir contigo — ver "Próximo paso".

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
- `velora.services.narration`, `velora.services.voice` — sin cambios.
- `velora.providers` (raíz), `velora.providers.text_generation`,
  `velora.providers.voice` — sin cambios.
- `velora.engines.story` — sin cambios.
- `velora.engines.narration_audio` — **nuevo**: `SceneAudio` (`index`,
  `audio: bytes`, `audio_format: str`), `StoryAudio` (`topic`,
  `scenes`), `NarrationAudioEngine`
  (`synthesize(story: Story) -> StoryAudio`). Envuelve un `VoiceService`
  inyectado; sintetiza cada escena de una `Story` en orden. Sin
  consumidor todavía dentro del código base.
- `velora.workflows.story` — sin cambios.

Ver `docs/architecture.md` para el detalle de cada símbolo.

## Componentes que NO existen todavía

Extensions. Tampoco Providers de imagen, video, música o traducción,
más Services de capacidad, más Engines (Subtitle, Timeline, Render,
Publish), ni más Workflows que `StoryWorkflow`. Ningún Workflow consume
todavía `velora.engines.narration_audio`.

## Decisiones vigentes (ADR)

- **ADR-0001** a **ADR-0014** — ver PRs anteriores; sin cambios.
- **ADR-0015** — `NarrationAudioEngine` es el segundo Engine, sobre
  `VoiceService`, mismo diagrama canónico que `StoryEngine` sobre
  `NarrationService`. A diferencia de `StoryEngine`, no tiene ninguna
  precondición propia (`synthesize()` recibe una `Story` ya validada por
  la capa anterior, no un `topic` crudo). `SceneAudio`/`StoryAudio`
  reflejan `Scene`/`Story` en su propio dominio (audio, no texto);
  `SceneAudio` no repite el texto de la escena, solo su `index`. Sin
  agregación de errores: la primera escena que falle detiene toda la
  operación. Vinculante para todo Engine futuro que reciba una `Story`
  ya construida: sin precondición propia sobre lo que la capa anterior
  ya validó.

## Criterios de aceptación vigentes

Desde un repositorio limpio:

```
git clone <repo>
uv sync
uv run velora
uv run pytest
```

Sin cambios respecto a PR-011. El Core mantiene cobertura de pruebas
≥90%; PR-012 cierra con 100%. `velora.engines.narration_audio` no tiene
consumidor en la CLI todavía — no hay comando `velora create ...` nuevo
en este PR.

## Próximo paso

Con `StoryEngine` y `NarrationAudioEngine` ya existiendo — dos Engines
reales, cada uno produciendo una mitad de lo que un video necesita
(texto dividido en escenas, audio de esas escenas) — el camino que
`PROJECT_CONTEXT.md` venía señalando desde PR-009 finalmente tiene
sentido: coordinarlos en un Workflow. Necesito tu decisión antes de
`Genera PR-013`:

1. **Extender `StoryWorkflow`** para que, tras construir la `Story` con
   `StoryEngine`, también la sintetice a audio con
   `NarrationAudioEngine` — `run(topic) -> Story` pasaría a devolver
   algo que incluya ambos (¿un nuevo tipo que combine `Story` +
   `StoryAudio`? ¿dos llamadas separadas que el llamador combina?). Esta
   es exactamente la decisión de diseño que ADR-0012 dejó pendiente:
   "revelaría si la forma actual de `StoryWorkflow` sigue siendo la
   correcta o necesita crecer".
2. **Un Workflow nuevo**, dejando `StoryWorkflow` como está (solo texto)
   y creando p. ej. `NarratedStoryWorkflow` que coordina ambos Engines
   desde cero — evita decidir si `StoryWorkflow` "crece" o no, a costa
   de tener dos Workflows con superposición parcial.
3. **Seguir ampliando horizontalmente** (tercer dominio de
   Provider/Service, p. ej. imagen) antes de resolver la orquestación.

Mi inclinación, si preguntas: opción 1 — extender `StoryWorkflow`. Es
exactamente la pregunta que ADR-0012 dejó abierta a propósito ("antes de
que exista un segundo Engine que coordinar"); ese segundo Engine ya
existe. Un Workflow nuevo con solapamiento parcial sería la misma
sobre-construcción que el manifiesto pide evitar en cada capa anterior.
Pero es tu llamada, y esta en particular vale la pena discutir antes de
que la construya — el tipo de resultado que `StoryWorkflow.run()`
devolvería es una decisión de diseño real, no solo mecánica.
