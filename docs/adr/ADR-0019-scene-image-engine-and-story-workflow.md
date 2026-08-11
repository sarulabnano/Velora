# ADR-0019: `SceneImageEngine` y `StoryWorkflow` extendido a tres Engines

## Status

Accepted

## Context

Tras PR-015 (`ImageService`, ADR-0018), `PROJECT_CONTEXT.md` dejaba
tres caminos: un Engine de imagen, extender `StoryWorkflow` una tercera
vez (dependiente del anterior), o persistir el audio a disco desde la
CLI. Se confirmó el Engine de imagen — exactamente la misma secuencia
que ya se siguió para voz (Provider → Service → **Engine** →
Workflow extendido, PR-010→PR-011→**PR-012**→PR-013), ahora aplicada a
imagen en dos pasos de un mismo PR: el Engine, y de inmediato la
extensión de `StoryWorkflow` que le da un consumidor real — la misma
razón por la que ADR-0016 no se pospuso tampoco tras ADR-0015.

`docs/VISION.md` no nombra un "Scene Image Engine" explícitamente
(nombra Story Engine, Subtitle Engine, Timeline Engine, Render Engine,
Publish Engine), pero el paso "generar imagenes" del Workflow de
ejemplo, justo después de "generar voz", necesita exactamente esta
pieza — el mismo razonamiento que ADR-0015 ya aplicó para justificar
`NarrationAudioEngine` sin un nombre correspondiente en la visión.

## Decision

### `SceneImageEngine`: mismo patrón exacto que `NarrationAudioEngine`

- **Entrada**: `Story`, no un `topic` crudo — mismo razonamiento que
  ADR-0015 (`NarrationAudioEngine.synthesize`): la capa anterior
  (`StoryEngine`) ya la validó. `illustrate()` no tiene ninguna
  precondición propia.
- **Tipos nuevos**: `SceneImage` (`index`, `image`, `image_format`) y
  `StoryImages` (`topic`, `scenes`) — mismo par que `SceneAudio`/
  `StoryAudio`: reflejan la forma de `Scene`/`Story` en el dominio
  imagen, sin repetir el texto de la escena (el `index` compartido
  basta para correlacionar).
- **Nombre del tipo contenedor, `StoryImages` (plural), no
  `StoryImage`**: a diferencia de "audio" (sustantivo no contable, que
  se lee natural en singular incluso cubriendo varias escenas —
  `StoryAudio`), "imágenes" de una historia son un conjunto contable,
  una por escena; el plural es el nombre preciso de lo que el tipo
  contiene. Es la única desviación deliberada del espejo textual
  perfecto con `SceneAudio`/`StoryAudio`.
- **Sin agregación de errores**: la primera escena que falle detiene
  toda la operación — mismo razonamiento que ADR-0015: ningún
  consumidor real necesita "imágenes parciales de una Story" todavía.
- **Depende de `ImageService`, nunca de `ImageProvider` directamente**:
  mismo diagrama canónico exacto que `NarrationAudioEngine →
  VoiceService` — `SceneImageEngine → ImageService → ImageProvider →
  openai`. El Engine nunca ve `velora.providers` ni `openai`.
- **Prompt de cada imagen**: el texto de la escena, tal cual, sin
  reescritura ni ingeniería de prompt — no hay todavía un consumidor
  real que necesite una traducción entre "texto narrado" y "prompt
  visual"; construir esa capa sin necesidad sería la misma
  sobre-construcción que el manifiesto pide evitar en cada capa
  anterior. Cuando exista ese consumidor, esa traducción tiene un lugar
  natural: dentro de `SceneImageEngine.illustrate()`, no en
  `ImageService` (que no debe saber que "prompt" viene de una escena
  narrada) ni en `StoryWorkflow` (que no debe conocer los detalles
  internos de cómo un Engine hace su trabajo).

### `StoryWorkflow`: tercer Engine coordinado, mismo orden documentado

`StoryWorkflow.__init__` recibe ahora `StoryEngine`,
`NarrationAudioEngine`, **y** `SceneImageEngine`, los tres inyectados.
`run()` construye la `Story`, la sintetiza, y la ilustra, en ese orden
— el mismo orden que `docs/VISION.md` lista en su pipeline de ejemplo
("dividir escenas" → "generar voz" → "generar imagenes"). A diferencia
del orden `StoryEngine` → `NarrationAudioEngine` (donde el segundo paso
depende genuinamente del primero, porque necesita las escenas), la
ilustración no depende del audio en ningún sentido — sintetizar y
ilustrar son independientes entre sí una vez que la `Story` existe.
Se documenta explícitamente en el docstring de `run()` que este orden
es el que ya estableció PR-013, no una dependencia real, dejando
constancia de que una paralelización futura de estos dos pasos no
rompería el contrato de ningún Engine.

### `NarratedStory`: compone el tercer resultado, mismo criterio que ADR-0016

`NarratedStory` gana un tercer campo, `images: StoryImages` — mismo
criterio exacto que ADR-0016 ya estableció para `audio`: ninguno de los
tres tipos, por separado, representa ya "texto, audio e imágenes
juntos"; el tipo compone los tres resultados de los tres Engines
directamente, sin duplicar ni aplanar sus campos.

### CLI: `create story` pasa a requerir las tres claves de API

Mismo patrón exacto que ADR-0016 ya estableció al agregar
`VELORA_ELEVENLABS_API_KEY`: `VeloraSettings` gana `openai_api_key:
str | None = None`, leído de `VELORA_OPENAI_API_KEY`, con el mismo
tratamiento opcional-hasta-el-punto-de-uso. `_run_create_story`
construye ahora la cadena completa de tres Providers/Services/Engines y
registra los tres Providers como `LifecycleComponent`s del mismo
`Runtime` dedicado. `_default_image_provider_factory` importa
`OpenAIImageProvider` de forma perezosa — mismo patrón que
`_default_voice_provider_factory` ya establece para `elevenlabs`.

La salida de la CLI ahora imprime, por escena: el texto, una línea con
tamaño/formato del audio, y una línea con tamaño/formato de la imagen —
extendiendo el formato que ADR-0016 ya introdujo para audio, sin
guardar ningún archivo a disco todavía (esa decisión sigue pendiente,
sin relación con este PR).

## Consequences

- `velora.engines.scene_image` no importa `velora.providers` ni
  `openai` en ningún punto — solo `velora.services.image` y
  `velora.engines.story` (para el tipo `Story` que recibe como
  entrada), exactamente el mismo diagrama que ya sigue
  `velora.engines.narration_audio`.
- `StoryWorkflow` es ahora el primer Workflow que coordina tres
  Engines — el mismo patrón "extender, no bifurcar" que ADR-0016 ya
  demostró para dos, ahora demostrado para tres.
- Cualquier código existente que construía `StoryWorkflow(story_engine,
  narration_audio_engine)` con dos argumentos deja de compilar: mismo
  tipo de cambio incompatible deliberado que ADR-0016 ya hizo al pasar
  de uno a dos argumentos.
- `velora create story` exige las tres claves de API desde este PR; un
  usuario que solo tenía configuradas las dos primeras verá un nuevo
  error `fatal` hasta que configure también `VELORA_OPENAI_API_KEY`.
- Con los tres pasos del pipeline de `docs/VISION.md` hasta "generar
  imagenes" ya coordinados por un único Workflow, el siguiente Engine
  natural (Subtitle, según `docs/VISION.md`) tendría, por primera vez,
  tanto un `StoryImages` como un `StoryAudio` reales de los que
  depender — no solo texto. Queda como decisión explícita para el
  siguiente PR, junto con la persistencia a disco que sigue pospuesta.
