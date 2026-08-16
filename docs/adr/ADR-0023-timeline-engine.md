# ADR-0023: `TimelineEngine` organiza los cuatro resultados en una secuencia alineada

## Status

Accepted

## Context

Con los subtítulos ya cronometrados con precisión sobre el audio real
(PR-019, ADR-0022), `PROJECT_CONTEXT.md` dejaba como camino principal
el siguiente paso del pipeline de ejemplo de `docs/VISION.md`:
"construir timeline", justo después de "generar imagenes" y antes de
"renderizar". `docs/VISION.md` describe el Timeline Engine en una sola
línea: "Organiza escenas" — mismo nivel de detalle escueto que tenía
Subtitle Engine antes de PR-018.

Hasta este PR, `StoryWorkflow` produce cuatro resultados en paralelo
(`story`, `audio`, `images`, `subtitles`), cada uno atribuible a su
propio Engine, correlacionados entre sí únicamente por compartir el
mismo `index` de escena. Un consumidor futuro (p. ej. un Render Engine)
que necesite, para cada escena, su audio, su imagen, y su ventana de
tiempo, tendría que correlacionar tres colecciones por su cuenta cada
vez. Ese es exactamente el trabajo que "organiza escenas" describe.

## Decision

### `TimelineEngine`: combina, no recalcula

`TimelineEngine.build(story: Story, audio: StoryAudio, images:
StoryImages, subtitles: StorySubtitles) -> Timeline` — toma los cuatro
resultados que los Engines anteriores ya construyeron y produce una
única secuencia de `TimelineScene`, una por escena, cada una con: el
texto, el audio y su formato, la imagen y su formato, y
`start_seconds`/`end_seconds`. Estos tiempos son exactamente los que
`SubtitleEngine` ya calculó a partir de la duración real del audio
(ADR-0022) — `TimelineEngine` los reutiliza, no los vuelve a medir: no
hay ninguna razón para que dos Engines midan la misma duración por
separado, y `SubtitleEngine` ya es la fuente de verdad para ese dato.

Sin Service ni Provider inyectado, mismo motivo que `SubtitleEngine`
(ADR-0021): no hay nada externo que llamar, solo reorganizar resultados
que ya existen.

### `TimelineScene` sí repite todos sus campos, a diferencia del resto

A diferencia de `SceneAudio`/`SceneImage`/`SceneSubtitle` — cada uno la
salida de un solo Engine, correlacionada de vuelta a la `Story` solo
por `index` — `TimelineScene` repite el texto, el audio, y la imagen
completos. Es deliberado: `TimelineScene` existe específicamente para
eliminar la necesidad de correlacionar cuatro colecciones a mano; un
`TimelineScene` que a su vez solo tuviera índices y hubiera que volver
a cruzar contra las otras cuatro estructuras no resolvería el problema
que este Engine existe para resolver.

### `NarratedStory.timeline` no es redundante con los otros cuatro campos

Se consideró si `Timeline` duplicaba lo que `NarratedStory` ya
expresaba. No es así: `story`/`audio`/`images`/`subtitles` son, cada
uno, la salida propia de un Engine, mantenida atribuible por separado;
`timeline` es la síntesis que `TimelineEngine` hace de los cuatro en la
secuencia única que un futuro paso de Render necesitaría — la misma
distinción que separa una tabla de hechos de una vista materializada
sobre ella. `NarratedStory` gana un quinto campo, `timeline: Timeline`,
mismo criterio de composición que ADR-0016/ADR-0019/ADR-0021 ya
establecieron.

### Validación estricta, no degradación con gracia — a diferencia de `SubtitleEngine`

Si una escena de `story.scenes` no tiene entrada correspondiente (por
`index`) en `audio`, `images`, o `subtitles`, `build()` lanza
`ValueError` de inmediato. Esto es deliberadamente distinto del
fallback silencioso que `SubtitleEngine.caption()` aplica cuando un
clip de audio no puede interpretarse (ADR-0022): ese caso es un fallo
externo *esperado* (un Provider con un formato inusual). Una escena
ausente de una de las cuatro colecciones aquí significa que los cuatro
argumentos, sencillamente, no describen la misma `Story` — un error de
invariante de quien llama al Engine, no algo de lo que degradarse con
gracia. A través de `StoryWorkflow`, esta precondición nunca puede
fallar en la práctica: los cuatro argumentos siempre provienen de la
misma `story` que el propio Workflow construyó.

### `StoryWorkflow`: quinto Engine, el primero que depende de los tres anteriores a la vez

`StoryWorkflow.__init__` recibe ahora también un `TimelineEngine`.
`run()` construye la `Story`, la sintetiza, la ilustra, la subtitula, y
por último construye el timeline — el único orden posible, ya que
`TimelineEngine.build()` necesita los tres resultados anteriores
completos antes de poder ejecutarse. Es el primer paso del pipeline que
depende de más de un Engine previo a la vez.

### CLI: `timeline.json`, un manifiesto legible por máquina

`_save_narrated_story` escribe ahora también `timeline.json`: una
lista, por escena, de `index`, `text`, `audio_file`, `image_file` (los
nombres de archivo que la propia función ya calcula con la convención
`scene_{index:03d}.{formato}` ya establecida), `start_seconds`, y
`end_seconds`. Los nombres de archivo son una decisión de persistencia
de la CLI, no algo que `Timeline`/`TimelineScene` deban conocer — misma
separación que ya mantiene `render_srt()` respecto a `StorySubtitles`
(ADR-0021): el Engine no decide nombres de archivo, la capa que
persiste sí. Este manifiesto es lo que le da a `output_dir` la
propiedad de poder alimentarse directamente a una herramienta externa
de renderizado sin que esa herramienta tenga que adivinar qué archivo
corresponde a qué escena o a qué instante de tiempo.

## Consequences

- `velora.engines.timeline` depende de `velora.engines.story`,
  `velora.engines.narration_audio`, `velora.engines.scene_image`, y
  `velora.engines.subtitle` — solo por sus tipos de resultado
  (`Story`, `StoryAudio`, `StoryImages`, `StorySubtitles`), nunca por
  su lógica. Es el primer Engine con dependencias de tipo hacia tres
  Engines distintos a la vez.
- Cualquier código existente que construía `StoryWorkflow` con cuatro
  argumentos deja de compilar: cambio incompatible deliberado, mismo
  criterio que ADR-0016/ADR-0019/ADR-0021/ADR-0022 ya aplicaron en
  cada extensión sucesiva.
- `velora create story` no requiere ninguna clave de API nueva.
- Con los cinco Engines del pipeline de ejemplo de `docs/VISION.md`
  hasta "construir timeline" ya coordinados, el siguiente paso
  documentado —"renderizar"— sería el primer Engine que produce un
  artefacto de salida real (video) en vez de datos estructurados que la
  CLI persiste directamente.
