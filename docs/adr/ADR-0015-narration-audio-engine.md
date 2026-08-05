# ADR-0015: `NarrationAudioEngine`, el segundo Engine

## Status

Accepted

## Context

Tras PR-011 (`VoiceService`), `PROJECT_CONTEXT.md` dejaba tres caminos:
extender `StoryWorkflow` directamente para que también sintetizara
audio, un Engine dedicado antes de tocar `StoryWorkflow`, o un tercer
dominio de Provider/Service. Se eligió el Engine dedicado: `StoryWorkflow`
depende hoy de `StoryEngine`, nunca de `NarrationService` directamente
(ADR-0012 — nunca se salta una capa del diagrama canónico de ADR-0008).
Hacerlo depender también de `VoiceService` directamente rompería esa
misma disciplina que `StoryWorkflow` ya sigue consigo mismo. Un Engine
de audio mantiene el diagrama limpio y le da a un `StoryWorkflow`
extendido (o a un Workflow nuevo) algo real que coordinar sin violar su
propia regla.

`docs/VISION.md` no nombra un "Narration Audio Engine" explícitamente
(nombra Story Engine, Subtitle Engine, Timeline Engine, Render Engine,
Publish Engine), pero el paso "generar voz" del Workflow de ejemplo
necesita exactamente esta pieza: convertir una `Story` (texto, ya
dividida en escenas) en audio, escena por escena, antes de que un futuro
Subtitle/Timeline Engine pueda trabajar con ella.

## Decision

### Entrada: `Story`, no un `topic` crudo

A diferencia de `StoryEngine.build_story(topic: str)`, que recibe una
cadena sin validar, `NarrationAudioEngine.synthesize(story: Story)`
recibe una `Story` ya construida — un objeto que `StoryEngine` ya
validó al construirlo (su `topic` ya no puede estar vacío por
construcción). Por eso `synthesize()` no tiene ninguna precondición
propia que verificar con `ValueError`: a diferencia de `StoryEngine`
(ADR-0011) y `NarrationService`/`VoiceService` (ADR-0010, ADR-0014),
este es el primer componente cuya entrada ya llega validada por la capa
anterior, en vez de ser el primero en validarla.

### Tipos nuevos: `SceneAudio`, `StoryAudio` — mismo par que `Scene`/`Story`

`SpeechResult` (`velora.providers.voice`) no lleva a qué escena
pertenece; sin un tipo nuevo, un llamador con varias escenas sintetizadas
no podría reconstruir el orden ni la correspondencia. `SceneAudio`
(`index`, `audio`, `audio_format`) y `StoryAudio` (`topic`, `scenes`)
reflejan exactamente la forma de `Scene`/`Story` — la versión en audio
de la misma idea, no una jerarquía nueva sin relación.

`SceneAudio` no repite el texto de la escena: quien llama a
`synthesize(story)` ya tiene la `Story` original con
`story.scenes[i].text`; el `index` compartido basta para correlacionar
ambas sin duplicar el dato. `audio_format` vive en cada `SceneAudio`,
no una sola vez en `StoryAudio`: es exactamente lo que cada
`SpeechResult` devolvió, sin inventar la garantía de que todas las
escenas comparten formato.

### Sin agregación de errores: falla en la primera escena que falle

Si `VoiceService.speak()` falla para alguna escena, `synthesize()` deja
propagar la excepción inmediatamente — no intenta sintetizar el resto
de las escenas ni acumula fallos parciales. No hay ningún caso de uso
real todavía que necesite "audio parcial de una Story" como resultado
válido; construir esa máquina de agregación sin un consumidor real que
la pida sería la misma sobre-construcción que el manifiesto pide evitar
en cada capa anterior.

### Depende de `VoiceService`, nunca de `VoiceProvider` directamente

Mismo diagrama canónico exacto que `StoryEngine → NarrationService`
(ADR-0008, ADR-0011): `NarrationAudioEngine → VoiceService →
VoiceProvider → elevenlabs`. El Engine nunca ve `velora.providers` ni
`elevenlabs`.

## Consequences

- `velora.engines.narration_audio` no importa `velora.providers` ni
  `elevenlabs` en ningún punto — solo `velora.services.voice` y
  `velora.engines.story` (para el tipo `Story` que recibe como entrada).
- Ningún Workflow existente cambia todavía: `StoryWorkflow` no conoce
  `NarrationAudioEngine`. Extenderlo (o crear un Workflow nuevo que
  coordine ambos Engines) queda como decisión explícita para el
  siguiente PR — la primera vez que un Workflow tendría más de un
  Engine real que coordinar.
- Cualquier Engine futuro que también reciba una `Story` ya construida
  (un Subtitle Engine, por ejemplo) sigue el mismo patrón: sin
  precondición propia sobre una entrada que la capa anterior ya validó,
  tipo de resultado propio que refleja `Scene`/`Story` en su propio
  dominio en vez de reutilizarlos directamente (el texto y el audio de
  una escena no son la misma cosa).
