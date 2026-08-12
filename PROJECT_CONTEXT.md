# PROJECT_CONTEXT

Este documento resume el estado actual de Velora. No duplica los ADR ni
`docs/VISION.md`; los referencia.

## Último PR

**PR-018 — Engines: `SubtitleEngine`; Workflows: `StoryWorkflow`
coordina sus cuatro Engines; CLI: persiste `story.srt`.**

## Milestone activa

**Engines / Workflows.** Los cuatro Engines del pipeline de ejemplo de
`docs/VISION.md` hasta "insertar subtítulos" están coordinados por
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
  `SubtitleEngine` (sin Provider, sin clave de API nueva). Gana el
  argumento `--words-per-minute` (por defecto `150.0`). Persiste un
  `story.srt` junto al resto de archivos, e imprime `Subtitles:
  story.srt`.
- `velora.runtime`, `velora.logging`, `velora.configuration` — sin
  cambios.
- `velora.services` (raíz), `velora.services.narration`,
  `velora.services.voice`, `velora.services.image` — sin cambios.
- `velora.providers` (raíz), `velora.providers.text_generation`,
  `velora.providers.voice`, `velora.providers.image` — sin cambios.
- `velora.engines.story`, `velora.engines.narration_audio`,
  `velora.engines.scene_image` — sin cambios.
- `velora.engines.subtitle` — **nuevo**: cuarto Engine, y el primero sin
  Service ni Provider inyectado. `SubtitleEngine.caption(story: Story)
  -> StorySubtitles`, estimando el tiempo de cada escena vía un ritmo
  de lectura configurable (`words_per_minute`, por defecto `150.0`) —
  no la duración real del audio. Tipos nuevos: `SceneSubtitle` (`index`,
  `text`, `start_seconds`, `end_seconds` — a diferencia de
  `SceneAudio`/`SceneImage`, sí repite el texto, porque el texto *es*
  el artefacto), `StorySubtitles` (`topic`, `scenes`). `render_srt()`
  renderiza a formato SubRip (.srt), como función separada del tipo de
  resultado.
- `velora.workflows.story` — **cambia**: `StoryWorkflow.__init__` recibe
  ahora también `SubtitleEngine`. `NarratedStory` gana un cuarto campo,
  `subtitles: StorySubtitles`. `run()` construye, sintetiza, ilustra, y
  subtitula, en ese orden — solo el primer paso es una dependencia
  genuina de los demás.

Ver `docs/architecture.md` para el detalle de cada símbolo.

## Estado real del producto — qué se puede hacer hoy

- **Texto + audio + imágenes + subtítulos, persistido a disco**:
  `velora create story` produce un directorio con `story.txt`,
  `story.srt`, y un archivo de audio y uno de imagen por escena — listo
  para cargar en un editor de video sin ningún paso manual adicional.
- El tiempo de los subtítulos es una **estimación** basada en el texto
  (ritmo de lectura configurable), no una medición del audio real
  generado — documentado explícitamente como limitación conocida en
  ADR-0021.

## Componentes que NO existen todavía

Extensions. Tampoco más Providers/Services de ningún dominio existente,
más dominios de Provider (video, música, traducción), más Engines
(Timeline, Render, Publish — ver `docs/VISION.md`), ni más Workflows
que `StoryWorkflow`. Ningún mecanismo para medir la duración real del
audio y ajustar el tiempo de los subtítulos en consecuencia — sigue
siendo una estimación por ritmo de lectura.

## Decisiones vigentes (ADR)

- **ADR-0001** a **ADR-0020** — ver PRs anteriores; sin cambios.
- **ADR-0021** — `SubtitleEngine`, el primer Engine sin Service ni
  Provider inyectado: no hay nada externo que llamar para estimar
  tiempo de lectura desde texto. Tiempo estimado por
  `words_per_minute` configurable, no por duración real del audio
  (decodificar audio para medir duración exacta es una dependencia
  nueva sin consumidor real que la pida todavía). `SceneSubtitle` sí
  repite el texto de la escena, a diferencia de `SceneAudio`/
  `SceneImage` — el texto es el artefacto, no hay payload binario
  sustituto. `render_srt()` vive separado del tipo de resultado, mismo
  principio de "tipo agnóstico de formato, renderizado aparte" en toda
  la capa de Engines. `StoryWorkflow` coordina ahora los cuatro
  Engines; `create story` no requiere ninguna clave de API nueva para
  este Engine, y persiste un único `story.srt` compartido (no uno por
  escena). Vinculante para cualquier Engine futuro que resulte ser
  puramente computacional: es una posición válida en el diagrama de
  ADR-0008, no una desviación de él.

## Criterios de aceptación vigentes

Desde un repositorio limpio:

```
git clone <repo>
uv sync
uv run velora
uv run pytest
```

El Core mantiene cobertura de pruebas ≥90%; PR-018 cierra con 100%.
`velora create story` sigue requiriendo las mismas tres claves de API
que en PR-016/PR-017 — `SubtitleEngine` no añade ninguna nueva.

## Próximo paso

Con los cuatro Engines del pipeline de ejemplo de `docs/VISION.md`
coordinados hasta "insertar subtítulos", los siguientes pasos de ese
mismo pipeline —"construir timeline" y "renderizar"— son los primeros
que dependerían de *todos* los resultados existentes a la vez, no solo
de uno nuevo. Caminos razonables para `Genera PR-019`:

1. **Medir la duración real del audio** para que el tiempo de los
   subtítulos deje de ser una estimación — cierra la limitación
   documentada en ADR-0021, con un consumidor real (los propios
   subtítulos) que ya lo necesita.
2. **Timeline Engine** (según `docs/VISION.md`) — el primer Engine que
   combinaría texto, audio, imágenes, y subtítulos en una estructura
   temporal única, en vez de cuatro resultados paralelos.
3. **Un cuarto dominio de Provider/Service** (video, música,
   traducción) — sigue disponible, aunque cada vez con menos urgencia:
   ya hay cuatro capacidades reales sin haber saturado ninguna con
   consumidores.

Mi inclinación, si preguntas: opción 1. Es la más barata de las tres
(no requiere un nuevo dominio ni una decisión de diseño grande) y
resuelve honestamente una limitación que este mismo PR dejó anotada en
vez de ocultarla. Pero, como en la decisión anterior, no hay una
urgencia clara — dime hacia dónde prefieres llevarlo y sigo.
