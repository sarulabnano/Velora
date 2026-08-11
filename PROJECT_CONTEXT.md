# PROJECT_CONTEXT

Este documento resume el estado actual de Velora. No duplica los ADR ni
`docs/VISION.md`; los referencia.

## Último PR

**PR-016 — Engines: `SceneImageEngine`; Workflows: `StoryWorkflow`
coordina sus tres Engines.**

## Milestone activa

**Workflows** (`StoryWorkflow`, ahora coordinando texto + audio +
imágenes). Próxima: por decidir contigo — ver "Próximo paso".

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
  `ImageProvider` (por defecto, `OpenAIImageProvider`) y lo registra
  como tercer `LifecycleComponent` del mismo `Runtime` dedicado.
  Requiere `VELORA_ANTHROPIC_API_KEY`, `VELORA_ELEVENLABS_API_KEY`, **y**
  `VELORA_OPENAI_API_KEY` — falla rápido con un mensaje `fatal` si falta
  cualquiera de las tres. Imprime, por escena: el texto, y una línea
  para el audio y otra para la imagen (tamaño en bytes, formato).
- `velora.runtime`, `velora.logging` — sin cambios.
- `velora.configuration` — **cambia**: `VeloraSettings` gana
  `openai_api_key: str | None = None`, leído de
  `VELORA_OPENAI_API_KEY` — mismo tratamiento opcional-hasta-el-punto-
  de-uso que las otras dos claves.
- `velora.services` (raíz), `velora.services.narration`,
  `velora.services.voice`, `velora.services.image` — sin cambios.
- `velora.providers` (raíz), `velora.providers.text_generation`,
  `velora.providers.voice`, `velora.providers.image` — sin cambios.
- `velora.engines.story`, `velora.engines.narration_audio` — sin
  cambios.
- `velora.engines.scene_image` — **nuevo**: tercer Engine.
  `SceneImageEngine.illustrate(story: Story) -> StoryImages`, generando
  una imagen por escena vía `ImageService` inyectado. Tipos nuevos:
  `SceneImage` (`index`, `image`, `image_format`), `StoryImages`
  (`topic`, `scenes`). Usa el texto de cada escena como prompt, tal
  cual, sin reescritura.
- `velora.workflows.story` — **cambia**: `StoryWorkflow.__init__` recibe
  ahora `StoryEngine`, `NarrationAudioEngine`, **y** `SceneImageEngine`.
  `NarratedStory` gana un tercer campo, `images: StoryImages`. `run()`
  construye, sintetiza, e ilustra, en ese orden.

Ver `docs/architecture.md` para el detalle de cada símbolo.

## Estado real del producto — qué se puede hacer hoy

Actualizado desde PR-015, ahora que las tres piezas están conectadas:

- **Solo texto**: `StoryEngine` por sí solo. Funciona.
- **Texto + audio**: `StoryEngine` + `NarrationAudioEngine` a mano, o
  construyendo `StoryWorkflow` sin pasar por la CLI. Funciona.
- **Texto + audio + imágenes**: **funciona de punta a punta**, tanto en
  Python directo (`StoryWorkflow` con los tres Engines) como desde la
  CLI (`velora create story`, que ahora requiere las tres claves de
  API). Nada se guarda a disco automáticamente — la CLI reporta tamaño
  y formato por escena, no escribe archivos.

## Componentes que NO existen todavía

Extensions. Tampoco más Providers de ningún dominio existente, más
dominios de Provider (video, música, traducción), más Engines
(Subtitle, Timeline, Render, Publish), ni más Workflows que
`StoryWorkflow`. Ningún mecanismo para persistir a disco lo que
`StoryWorkflow` produce (ni audio ni imágenes) — `create story` lo
reporta, no lo guarda.

## Decisiones vigentes (ADR)

- **ADR-0001** a **ADR-0018** — ver PRs anteriores; sin cambios.
- **ADR-0019** — `SceneImageEngine`, mismo patrón exacto que ADR-0015
  (`NarrationAudioEngine`): entrada `Story` ya validada, sin
  precondición propia, sin agregación de errores, depende de
  `ImageService` nunca de `ImageProvider` directamente. Tipo contenedor
  nombrado `StoryImages` (plural), no `StoryImage` — única desviación
  deliberada del espejo con `SceneAudio`/`StoryAudio`, porque "imágenes"
  es un sustantivo contable y "audio" no. El prompt de cada imagen es
  el texto de la escena tal cual, sin reescritura, hasta que exista un
  consumidor real que la necesite. `StoryWorkflow` coordina ahora los
  tres Engines, en el orden que documenta `docs/VISION.md`;
  `NarratedStory` compone los tres resultados. `create story` exige las
  tres claves de API. Vinculante para cualquier Engine futuro que reciba
  una `Story` ya construida: mismo patrón, un nombre de tipo contenedor
  elegido por precisión gramatical del dominio, no copiado
  mecánicamente.

## Criterios de aceptación vigentes

Desde un repositorio limpio:

```
git clone <repo>
uv sync
uv run velora
uv run pytest
```

El Core mantiene cobertura de pruebas ≥90%; PR-016 cierra con 100%.
`velora create story --topic "..."` ahora requiere las tres claves de
API (`VELORA_ANTHROPIC_API_KEY`, `VELORA_ELEVENLABS_API_KEY`,
`VELORA_OPENAI_API_KEY`) en el entorno para completarse con éxito.

## Próximo paso

Con los tres pasos del pipeline de `docs/VISION.md` hasta "generar
imagenes" ya coordinados por `StoryWorkflow`, quedan varios caminos
razonables para `Genera PR-017` — no mutuamente excluyentes:

1. **Persistir a disco desde la CLI** (audio e imágenes, no solo
   reportar tamaño/formato) — sigue pendiente desde PR-013, pospuesta
   tres veces ya. Es el primer resultado verdaderamente entregable de
   todo el pipeline construido hasta ahora.
2. **Un Engine nuevo que dependa de los tres resultados existentes**
   (p. ej. Subtitle Engine, según `docs/VISION.md`) — por primera vez
   hay tanto `StoryAudio` como `StoryImages` reales de los que depender,
   no solo texto.
3. **Un cuarto dominio de Provider/Service** (video, música,
   traducción) — sigue disponible, aunque ya se demostró tres veces
   que conviene darle a cada dominio un consumidor real antes de abrir
   uno nuevo.

Mi inclinación, si preguntas: opción 1. Es la más pospuesta de las tres,
y sin ella, todo lo construido hasta ahora sigue siendo una
demostración interna — nada de lo que `StoryWorkflow` produce hoy
sobrevive fuera de la sesión que lo invocó. Pero, igual que en
decisiones anteriores de secuencia (no de diseño concreto), dímelo y
sigo.
