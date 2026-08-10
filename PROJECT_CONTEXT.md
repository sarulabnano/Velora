# PROJECT_CONTEXT

Este documento resume el estado actual de Velora. No duplica los ADR ni
`docs/VISION.md`; los referencia.

## Último PR

**PR-013 — `StoryWorkflow` extendido: coordina `StoryEngine` y
`NarrationAudioEngine`.**

## Milestone activa

**Workflows** (primer Workflow, `StoryWorkflow`, coordinando ya sus dos
Engines reales). Próxima: por decidir contigo — ver "Próximo paso".

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
- `velora.cli` — **cambia**: `create story` construye ahora también un
  `VoiceProvider` (por defecto, `ElevenLabsVoiceProvider`) y lo registra
  como segundo `LifecycleComponent` del mismo `Runtime` dedicado que ya
  usaba para el `TextGenerationProvider`. Requiere
  `VELORA_ANTHROPIC_API_KEY` **y** `VELORA_ELEVENLABS_API_KEY` — falla
  rápido con un mensaje `fatal` si falta cualquiera de las dos, antes de
  construir nada. Imprime, por escena: el texto y una línea con el
  tamaño en bytes y el formato del audio sintetizado.
- `velora.runtime` — sin cambios funcionales en este PR.
- `velora.configuration` — **cambia**: `VeloraSettings` gana
  `elevenlabs_api_key: str | None = None`, leído de
  `VELORA_ELEVENLABS_API_KEY` — mismo tratamiento opcional-hasta-el-
  punto-de-uso que `anthropic_api_key`.
- `velora.logging` — sin cambios funcionales en este PR.
- `velora.services` (raíz) — Services de infraestructura, sin cambios.
- `velora.services.narration`, `velora.services.voice` — sin cambios.
- `velora.providers` (raíz), `velora.providers.text_generation`,
  `velora.providers.voice` — sin cambios.
- `velora.engines.story` — sin cambios.
- `velora.engines.narration_audio` — sin cambios; ya tiene consumidor
  (ver `velora.workflows.story`, abajo).
- `velora.workflows.story` — **cambia**: `StoryWorkflow.__init__` recibe
  ahora un `StoryEngine` **y** un `NarrationAudioEngine`, ambos
  inyectados. `run(topic, *, max_tokens=1024)` construye la `Story` y
  después la sintetiza a audio, en ese orden, devolviendo un
  `NarratedStory` **nuevo** (`story: Story`, `audio: StoryAudio`) en vez
  de una `Story` sola. Sin agregación de resultado parcial: una falla
  sintetizando propaga el error y no devuelve nada, misma postura que
  `NarrationAudioEngine` ya tenía escena por escena.

Ver `docs/architecture.md` para el detalle de cada símbolo.

## Componentes que NO existen todavía

Extensions. Tampoco Providers de imagen, video, música o traducción,
más Services de capacidad, más Engines (Subtitle, Timeline, Render,
Publish), ni más Workflows que `StoryWorkflow`. Ningún mecanismo para
guardar el audio sintetizado a disco desde la CLI — `create story`
reporta tamaño y formato por escena, no escribe archivos.

## Decisiones vigentes (ADR)

- **ADR-0001** a **ADR-0015** — ver PRs anteriores; sin cambios.
- **ADR-0016** — `StoryWorkflow` coordina `StoryEngine` y
  `NarrationAudioEngine` (opción "extender", confirmada sobre las tres
  alternativas que dejaba abiertas PR-012). Ambos Engines se inyectan;
  `run()` construye la `Story` y luego la sintetiza, en ese orden. El
  resultado es un `NarratedStory` nuevo que compone `Story` + `StoryAudio`
  sin duplicar campos — no una tupla sin nombre, no una `Story`
  enriquecida. Sin resultado parcial ante un error: se propaga tal cual.
  `create story` pasa a requerir ambas claves de API y registra ambos
  Providers como `LifecycleComponent`s del mismo `Runtime` dedicado.
  Vinculante para cualquier Workflow futuro que coordine más de un
  Engine: mismo patrón (Engines inyectados, tipo de resultado que
  compone en vez de aplanar, sin resultado parcial ante error).

## Criterios de aceptación vigentes

Desde un repositorio limpio:

```
git clone <repo>
uv sync
uv run velora
uv run pytest
```

El Core mantiene cobertura de pruebas ≥90%; PR-013 cierra con 100%.
`velora create story --topic "..."` ahora requiere tanto
`VELORA_ANTHROPIC_API_KEY` como `VELORA_ELEVENLABS_API_KEY` en el
entorno para completarse con éxito (antes solo requería la primera).

## Próximo paso

Con `StoryWorkflow` coordinando ya sus dos Engines, y sin ningún
consumidor todavía del audio más allá de imprimir su tamaño/formato,
quedan dos caminos razonables para `Genera PR-014` — no son
mutuamente excluyentes, pero conviene decidir el orden:

1. **Persistir el audio a disco desde la CLI** (`create story` escribe
   un archivo por escena, o uno combinado, en vez de solo reportar
   bytes) — el primer resultado tangible y usable de todo el pipeline
   construido hasta ahora, sin requerir ningún componente nuevo del
   roadmap (Foundation → ... → Workflows ya cubre lo necesario).
2. **Seguir horizontal dentro de Engines**: un tercer dominio
   (imagen, subtítulos) antes de que `StoryWorkflow`/`NarratedStory`
   crezcan de nuevo — mantiene la disciplina de "un Engine a la vez"
   que ya rigió PR-011→PR-012, ahora aplicada a Workflows en vez de a
   Engines sueltos.

Mi inclinación, si preguntas: opción 1. Sin ella, "coordinar dos
Engines" sigue siendo una demostración interna — nada que `uv run
velora create story` produzca hoy sobrevive fuera de la terminal. Pero
a diferencia de la decisión de PR-013 (que sí exigía elegir una forma
de tipo concreta antes de escribir código), esta es más una cuestión de
secuencia que de diseño, así que dímelo y sigo.
