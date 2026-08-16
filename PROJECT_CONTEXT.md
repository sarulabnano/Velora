# PROJECT_CONTEXT

Este documento resume el estado actual de Velora. No duplica los ADR ni
`docs/VISION.md`; los referencia.

## Último PR

**PR-020 — Engines: `TimelineEngine`; Workflows: `StoryWorkflow`
coordina sus cinco Engines; CLI: persiste `timeline.json`.**

## Milestone activa

**Engines / Workflows.** Los cinco Engines del pipeline de ejemplo de
`docs/VISION.md` hasta "construir timeline" están coordinados por
`StoryWorkflow`. Próxima: por decidir contigo — ver "Próximo paso".

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
  `TimelineEngine` (sin Provider, sin clave de API nueva). Persiste un
  `timeline.json` junto al resto de archivos, e imprime `Timeline:
  timeline.json`.
- `velora.runtime`, `velora.logging`, `velora.configuration` — sin
  cambios.
- `velora.services` (raíz), `velora.services.narration`,
  `velora.services.voice`, `velora.services.image` — sin cambios.
- `velora.providers` (raíz), `velora.providers.text_generation`,
  `velora.providers.voice`, `velora.providers.image` — sin cambios.
- `velora.engines.story`, `velora.engines.narration_audio`,
  `velora.engines.scene_image`, `velora.engines.subtitle` — sin
  cambios.
- `velora.engines.timeline` — **nuevo**: quinto Engine, y el primero
  que depende de tres Engines anteriores a la vez (por tipo, no por
  lógica). `TimelineEngine.build(story, audio, images, subtitles) ->
  Timeline`, combinando los cuatro resultados en una secuencia única
  alineada por escena. Reutiliza el `start_seconds`/`end_seconds` que
  `SubtitleEngine` ya calculó — no los vuelve a medir. Tipos nuevos:
  `TimelineScene` (repite todos sus campos, a diferencia de
  `SceneAudio`/`SceneImage`/`SceneSubtitle` — existe precisamente para
  no tener que correlacionar cuatro colecciones a mano), `Timeline`
  (`topic`, `scenes`). Lanza `ValueError` si una escena falta en
  cualquiera de las cuatro entradas — a diferencia del fallback de
  `SubtitleEngine`, esto es un error de invariante del llamador, no un
  fallo externo esperado.
- `velora.workflows.story` — **cambia**: `StoryWorkflow.__init__` recibe
  ahora también `TimelineEngine`. `NarratedStory` gana un quinto campo,
  `timeline: Timeline`. `run()` construye el timeline al final, después
  de que síntesis, ilustración, y subtitulado ya completaron — es el
  único paso que necesita los tres a la vez.

Ver `docs/architecture.md` para el detalle de cada símbolo.

## Estado real del producto — qué se puede hacer hoy

- **Texto + audio + imágenes + subtítulos + timeline, persistido a
  disco**: `velora create story` produce un directorio con `story.txt`,
  `story.srt`, `timeline.json` (manifiesto legible por máquina: por
  escena, nombres de archivo de audio/imagen y su ventana de tiempo), y
  un archivo de audio y uno de imagen por escena — listo para
  alimentarse a una herramienta externa de renderizado sin adivinar qué
  archivo corresponde a qué escena.

## Componentes que NO existen todavía

Extensions. Tampoco más Providers/Services de ningún dominio existente,
más dominios de Provider (video, música, traducción), más Engines
(Render, Publish — ver `docs/VISION.md`), ni más Workflows que
`StoryWorkflow`. Ningún mecanismo para renderizar el timeline a un
video real — `timeline.json` es el manifiesto, no el video.

## Decisiones vigentes (ADR)

- **ADR-0001** a **ADR-0022** — ver PRs anteriores; sin cambios.
- **ADR-0023** — `TimelineEngine`, quinto Engine, sin Service ni
  Provider. Combina `Story`/`StoryAudio`/`StoryImages`/`StorySubtitles`
  en una secuencia única de `TimelineScene` (que sí repite todos sus
  campos, a diferencia del resto de tipos "Scene*"), reutilizando el
  tiempo ya calculado por `SubtitleEngine` sin remedirlo. Valida
  estrictamente (`ValueError`) que las cuatro entradas describan las
  mismas escenas — a diferencia de la degradación con gracia de
  `SubtitleEngine`, una escena faltante aquí es un error de invariante
  del llamador, no un fallo externo esperado. `StoryWorkflow` lo ejecuta
  al final, siendo el primer paso que depende de tres Engines
  anteriores a la vez. `create story` persiste `timeline.json` —
  manifiesto con nombres de archivo (decisión de la CLI, no del
  Engine) y timing por escena. Vinculante para cualquier Engine futuro
  que combine resultados de varios Engines anteriores: reutilizar
  datos ya calculados en vez de remedir, y decidir explícitamente si
  las entradas ausentes se degradan con gracia o son un error de
  invariante — documentando por qué en cada caso.

## Criterios de aceptación vigentes

Desde un repositorio limpio:

```
git clone <repo>
uv sync
uv run velora
uv run pytest
```

El Core mantiene cobertura de pruebas ≥90%; PR-020 cierra con 100%.
`velora create story` sigue requiriendo las mismas tres claves de API
que en PR-016/PR-017/PR-018/PR-019 — `TimelineEngine` no añade ninguna
nueva.

## Próximo paso

Con los cinco Engines del pipeline de ejemplo de `docs/VISION.md`
coordinados hasta "construir timeline", el siguiente paso documentado
es "renderizar" — el primer Engine que produciría un artefacto de
salida real (un archivo de video) en vez de datos estructurados que la
CLI simplemente persiste. Caminos razonables para `Genera PR-021`:

1. **Render Engine** (según `docs/VISION.md`) — combina el `Timeline`
   en un video real. Esto probablemente requiere una decisión de
   diseño mayor que las anteriores: ¿qué herramienta de render usar
   (ffmpeg vía subproceso, una librería Python)?, ¿qué formato de
   salida?, ¿es un Provider (herramienta externa intercambiable) o
   lógica propia del Engine?
2. **Un cuarto dominio de Provider/Service** (video, música,
   traducción) — sigue disponible.
3. **Publish Engine** — adelantarse al paso final del pipeline de
   ejemplo, aunque sin un Render Engine todavía no hay nada tangible
   que publicar.

Mi inclinación, si preguntas: opción 1, pero con una advertencia real
esta vez — a diferencia de Subtitle/Timeline (ambos resueltos con
lógica pura, sin dependencias nuevas más allá de `mutagen`), un Render
Engine probablemente sí necesita una decisión de Provider genuina
(¿ffmpeg?, ¿alguna API de render en la nube?) del mismo calibre que la
de PR-014 (elegir OpenAI para imágenes). Vale la pena que decidas con
más contexto antes de que yo elija por defecto.
