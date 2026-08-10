# ADR-0016: `StoryWorkflow` extendido con `NarrationAudioEngine`

## Status

Accepted

## Context

Tras PR-012 (`NarrationAudioEngine`, ADR-0015), `PROJECT_CONTEXT.md`
dejaba tres caminos para PR-013, todos igualmente reales ahora que
existen dos Engines: extender `StoryWorkflow` para que `run(topic)`
devuelva texto y audio combinados; un Workflow nuevo
(`NarratedStoryWorkflow`) que deje `StoryWorkflow` intacto; o seguir
horizontal (un tercer dominio) antes de resolver la orquestación. Se
confirmó la primera opción — la misma que ADR-0012 había dejado
anotada como la más probable ("revelaría si la forma actual de
`StoryWorkflow` sigue siendo la correcta o necesita crecer").

`docs/VISION.md` describe los Workflows como la capa que "conecta
todos los motores": con un segundo Engine real, `StoryWorkflow` es
ahora el primer lugar del código donde esa descripción es literalmente
cierta, no solo aspiracional (ADR-0012 ya señaló que un solo Engine no
alcanzaba para demostrarlo).

## Decision

### Coordinar, no reemplazar: `StoryWorkflow` gana un segundo Engine inyectado

`StoryWorkflow.__init__` pasa de recibir un `StoryEngine` a recibir un
`StoryEngine` y un `NarrationAudioEngine`, ambos inyectados — nunca
construidos internamente, mismo principio que ya regía para el primero
(ADR-0012). `run(topic, *, max_tokens=1024)` primero llama a
`story_engine.build_story(topic, max_tokens=max_tokens)` y después a
`narration_audio_engine.synthesize(story)`, en ese orden: es el único
orden posible, ya que sintetizar audio necesita las escenas que el
primer paso produce, y es el mismo orden que el pipeline de ejemplo de
`docs/VISION.md` ya lista ("dividir escenas" antes de "generar voz").

No hay un tercer camino de "Workflow nuevo, `StoryWorkflow` intacto":
mantener dos Workflows —uno solo-texto, otro texto+audio— duplicaría
casi toda su lógica (misma llamada a `StoryEngine`, mismas excepciones
propagadas) por una diferencia de una sola llamada adicional. Ningún
llamador real necesita hoy un `StoryWorkflow` que produzca *solo*
texto — el propio `PROJECT_CONTEXT.md` de PR-012 registraba la
inclinación por extender, no bifurcar.

### Tipo de retorno: `NarratedStory`, que compone `Story` y `StoryAudio` sin duplicar campos

`run()` devuelve un `NarratedStory` nuevo (`velora.workflows.story`)
con dos campos: `story: Story` y `audio: StoryAudio` — no una `Story`
enriquecida con un campo de audio opcional, ni un tipo plano que
repita `topic`/`scenes` por su cuenta. Ninguno de los dos tipos
existentes, por separado, representa ya "texto y audio juntos"; crear
un tercer tipo que sencillamente los empareja es la misma decisión que
ADR-0015 ya tomó para `SceneAudio`/`StoryAudio` frente a
`Scene`/`Story` (reflejar la forma existente, no inventar una
jerarquía nueva) — aquí aplicada componiendo en vez de espejando.

Se descartó devolver una tupla `(Story, StoryAudio)` sin nombre: un
`NarratedStory` con atributos nombrados es autodescriptivo en el sitio
de la llamada (`narrated_story.audio.scenes`, no `result[1].scenes`),
y es el mismo criterio que ADR-0012 ya aplicó al preferir reutilizar
`Story` en vez de envolverlo sin necesidad — aquí la necesidad sí
existe (dos resultados reales, no uno), así que el tipo nuevo se
justifica.

### Manejo de errores: sin resultado parcial, mismo patrón que el Engine que ya lo estableció

`StoryWorkflow.run()` no captura ni envuelve ningún error: propaga
`ValueError` (precondición de `StoryEngine`) y `VeloraProviderError`
(de cualquiera de los dos Providers subyacentes) tal cual, exactamente
igual que hacía a través de PR-012 (ADR-0012). Si `synthesize()` falla
a mitad de las escenas, no se devuelve un `NarratedStory` con audio
parcial ni con la `Story` sola — la misma postura de "todo o nada" que
`NarrationAudioEngine` ya aplica escena por escena (ADR-0015),
extendida un nivel más arriba.

### CLI: `create story` pasa a requerir ambas claves de API

Puesto que `StoryWorkflow` ahora necesita un `VoiceProvider` además
del `TextGenerationProvider`, y `_run_create_story` construye toda la
cadena de dependencias él mismo (ADR-0012), `velora create story` deja
de funcionar únicamente con `VELORA_ANTHROPIC_API_KEY`: también exige
`VELORA_ELEVENLABS_API_KEY`, verificada de la misma forma "fail fast
antes de construir nada" que ya se aplicaba a la primera clave.
`VeloraSettings` gana `elevenlabs_api_key: str | None = None` — mismo
tratamiento opcional-hasta-el-punto-de-uso que `anthropic_api_key`
(ADR-0012): el smoke-run por defecto sigue sin necesitar ninguna de
las dos.

`_default_voice_provider_factory` importa `ElevenLabsVoiceProvider` de
forma perezosa, dentro del cuerpo de la función — mismo patrón que
`_default_text_generation_provider_factory` ya establece para
`anthropic` (ADR-0012), para que `velora.cli` en general (incluidos
`--version` y el smoke-run) nunca requiera el extra `velora[elevenlabs]`
para quien no lo instaló.

El `VoiceProvider` se registra como un segundo `LifecycleComponent` del
mismo `Runtime` dedicado que `create story` ya construye para el
`TextGenerationProvider` (ADR-0012) — no un `Runtime` propio: ambos
Providers comparten el mismo ciclo de vida de proceso, y `Runtime` ya
acepta una secuencia de componentes.

### Salida de la CLI: información de audio por escena, sin reproducir el audio

`_run_create_story` sigue imprimiendo el texto de cada escena como
hasta PR-012, y añade una línea por escena con el tamaño en bytes y el
formato del audio sintetizado (p. ej. `(48213 bytes, mp3)`) — suficiente
para confirmar que la síntesis ocurrió, sin intentar todavía guardar el
audio a disco (eso pertenece a una decisión de CLI futura, cuando haya
un caso de uso real de "exportar", no a esta ADR).

## Consequences

- `StoryWorkflow` es ahora el primer Workflow que coordina más de un
  Engine — la forma que `docs/VISION.md` describe para todo Workflow,
  no ya un caso especial de un solo Engine (ADR-0012).
- Cualquier código existente que construía `StoryWorkflow(story_engine)`
  con un solo argumento deja de compilar: es un cambio incompatible
  deliberado, no aditivo — no existe una versión "solo texto" que
  mantener en paralelo (ver más arriba, "Coordinar, no reemplazar").
- `velora create story` exige ambas claves de API desde este PR; un
  usuario que solo tenía configurada `VELORA_ANTHROPIC_API_KEY` verá
  un nuevo error `fatal` hasta que configure también
  `VELORA_ELEVENLABS_API_KEY`.
- Los tests de `StoryWorkflow` inyectan Providers falsos para ambos
  dominios (texto y voz) — nunca hacen una llamada HTTP real — mismo
  patrón de frontera simulada que ya usan los tests de `StoryEngine` y
  `NarrationAudioEngine` (ADR-0011, ADR-0015).
- Un futuro tercer Engine (imagen, video, ...) que se sume al mismo
  Workflow sigue este mismo patrón: Engine inyectado, campo nuevo en
  `NarratedStory` (o un tipo que lo reemplace si la forma deja de
  alcanzar), sin romper la disciplina de capas de ADR-0008/ADR-0012.
