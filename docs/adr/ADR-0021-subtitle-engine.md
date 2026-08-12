# ADR-0021: `SubtitleEngine` — el primer Engine sin Provider

## Status

Accepted

## Context

`docs/VISION.md` lista "Subtitle Engine — Genera subtítulos" entre sus
ejemplos de Engine, sin más detalle sobre cómo debe calcularse el
tiempo de cada subtítulo. Ningún dominio de Provider para subtítulos
existe ni se sugiere en `docs/VISION.md` (a diferencia de texto, voz, e
imagen, cada uno con su propia lista de proveedores concretos) — la
generación de subtítulos, en su forma más simple, no requiere ningún
servicio externo: basta con el texto que `StoryEngine` ya produjo y una
estimación de cuánto tarda en decirse.

## Decision

### Sin Provider ni Service: el primer Engine puramente computacional

`SubtitleEngine` no recibe ningún Service inyectado — a diferencia de
`StoryEngine`, `NarrationAudioEngine`, y `SceneImageEngine`, no hay
nada externo que llamar. `caption(story: Story) -> StorySubtitles`
opera enteramente sobre datos que el llamador ya tiene. Esto no viola
el diagrama canónico de ADR-0008 (Engines → Services → Providers): ese
diagrama describe la dirección permitida de las dependencias, no exige
que cada Engine tenga una. Un Engine sin Service es una posición válida
dentro de ese diagrama, simplemente en el extremo que no necesita
descender ninguna capa.

### Tiempo estimado por ritmo de lectura, no por duración real del audio

Cada escena obtiene una duración estimada de `palabras / words_per_minute
* 60` segundos, con `words_per_minute` configurable en el constructor
(por defecto, `150.0` — un ritmo de narración típico, documentado como
tal, no medido). Se consideró usar la duración real del audio que
`NarrationAudioEngine` ya produce (`SceneAudio.audio`, bytes de MP3),
pero eso exigiría decodificar el audio (una dependencia nueva, p. ej.
`mutagen` o similar, solo para leer metadata de duración) por una
precisión que ningún consumidor real pide todavía — la misma disciplina
de "no construir antes de que exista una necesidad real" que
`StoryEngine` ya aplicó al no apuntar a un conteo exacto de escenas
(ADR-0011). Cuando exista un consumidor que necesite sincronización
real cuadro a cuadro (p. ej. un futuro Render Engine), medir la
duración real del audio es la extensión natural — documentada aquí como
la limitación conocida, no oculta.

### `SceneSubtitle` repite el texto, a diferencia de `SceneAudio`/`SceneImage`

`SceneAudio` y `SceneImage` deliberadamente no repiten el texto de la
escena (ADR-0015, ADR-0019): el `index` basta para correlacionar,
porque el artefacto real (bytes de audio o imagen) sustituye al texto
como el contenido que importa. `SceneSubtitle` es distinto: el texto
*es* el artefacto — no hay ningún payload binario separado que un
llamador pudiera leer en su lugar. Omitirlo haría que `SceneSubtitle`
fuera inútil sin conservar también la `Story` original junto a él.

### Renderizado a SRT: función separada, no parte del tipo de resultado

`SubtitleEngine.caption()` devuelve `StorySubtitles`, un tipo tipado y
agnóstico de formato — no una cadena de texto ya formateada. El
renderizado a SubRip (`.srt`) vive en una función aparte,
`render_srt()`, en su propio módulo (`velora.engines.subtitle._srt`) —
misma separación que ya existe entre "resultado tipado" y "cómo se
imprime" en el resto de `velora.engines`: el Engine no decide el
formato de salida, un consumidor lo hace. Un formato futuro (WebVTT,
por ejemplo) tendría su propia función paralela, sin tocar
`SubtitleEngine` ni `StorySubtitles`.

### `StoryWorkflow`: cuarto Engine coordinado, sin dependencia entre pasos

`StoryWorkflow.__init__` recibe ahora también un `SubtitleEngine`.
`run()` construye la `Story`, la sintetiza, la ilustra, y la subtitula,
en ese orden — mismo razonamiento que ADR-0019 ya estableció para
síntesis e ilustración: el orden es el que documenta el pipeline de
ejemplo de `docs/VISION.md`, pero ninguno de los tres pasos posteriores
a `StoryEngine` depende de los otros, solo de la `Story` ya construida.
`NarratedStory` gana un cuarto campo, `subtitles: StorySubtitles` —
mismo criterio de composición que ADR-0016 y ADR-0019 ya establecieron.

### CLI: sin nueva clave de API, un archivo compartido en vez de uno por escena

`velora create story` construye `SubtitleEngine` directamente, sin
factory de Provider que inyectar ni clave de API que validar — es el
primer Engine del pipeline que no exige nada nuevo del entorno. Gana un
argumento `--words-per-minute` (por defecto, `150.0`, igual que el
Engine) para que el usuario pueda ajustar el ritmo estimado sin tocar
código. `_save_narrated_story` escribe un único `story.srt` (no uno por
escena, a diferencia de audio e imagen): un archivo `.srt` ya contiene
sus propios límites de escena como cues numerados; partirlo por escena
solo dificultaría cargarlo como una sola pista de subtítulos en un
editor de video.

## Consequences

- `velora.engines.subtitle` no importa `velora.services` ni
  `velora.providers` en ningún punto — solo `velora.engines.story`,
  para el tipo `Story` que recibe como entrada. Es la dependencia más
  ligera de cualquier Engine en el proyecto hasta ahora.
- `SubtitleEngine.caption()` nunca puede fallar por un error de
  Provider (`VeloraProviderError`) — su única fuente de error es la
  validación de `words_per_minute` en el constructor. `StoryWorkflow`
  documenta esto explícitamente: solo síntesis e ilustración pueden
  fallar por causas externas.
- El tiempo de cada subtítulo es una estimación, no una medición —
  documentado como tal en el docstring del Engine y en este ADR, para
  que cualquier consumidor futuro que necesite precisión real sepa
  exactamente qué reemplazar y por qué no se construyó así desde el
  principio.
- Con los cuatro Engines del pipeline de `docs/VISION.md` hasta
  "generar imagenes"/"insertar subtítulos" ya coordinados, los pasos
  que siguen en el pipeline de ejemplo — "construir timeline" y
  "renderizar" — son los primeros que dependerían de *todos* los
  resultados existentes a la vez (texto, audio, imágenes, y
  subtítulos), no solo de uno nuevo.
