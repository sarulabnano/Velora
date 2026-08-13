# ADR-0022: Subtítulos cronometrados por la duración real del audio

## Status

Accepted

## Context

ADR-0021 (PR-018) estimaba el tiempo de cada subtítulo a partir de un
ritmo de lectura configurable (`words_per_minute`) aplicado al conteo
de palabras del texto, documentando explícitamente que esto era una
limitación conocida: no medía la duración real del audio que
`NarrationAudioEngine` ya produce para esa misma escena.

Se confirmó medir la duración real, con una observación adicional del
usuario: el ritmo de lectura (`words_per_minute`) debería ser
consistente entre subtítulos y generación de audio, pero la mayoría de
los generadores de voz (incluido `ElevenLabsVoiceProvider`, el único
integrado hoy) no exponen un parámetro de "palabras por minuto" — el
ritmo real de la voz sintetizada lo decide el modelo de voz, no algo
que `VoiceService`/`VoiceProvider` puedan fijar de antemano. Dado que
no se puede *igualar* el ritmo, medir la duración real después del
hecho es la única forma de que los subtítulos coincidan genuinamente
con el audio.

## Decision

### Medir, no estimar: `measure_duration_seconds` sobre los bytes ya generados

`SubtitleEngine.caption()` cambia su firma a `caption(story: Story,
audio: StoryAudio) -> StorySubtitles` — recibe también el
`StoryAudio` que `NarrationAudioEngine` ya produjo. Para cada escena,
busca el `SceneAudio` correspondiente por `index` y mide su duración
real con `measure_duration_seconds` (nuevo, en
`velora.engines.subtitle._duration`), en vez de estimarla por conteo de
palabras.

### `mutagen`: primera dependencia base no opcional del proyecto

`measure_duration_seconds` usa `mutagen` para leer la duración desde
los metadatos del contenedor de audio (sin decodificar el audio
completo) — funciona directamente sobre los `bytes` en memoria que
`SceneAudio.audio` ya contiene, sin necesitar nombre de archivo ni
pista de formato: `mutagen` detecta el contenedor por sus propios bytes
mágicos.

Se agrega como dependencia **base** (`dependencies = ["mutagen>=1.47,<2"]`
en `pyproject.toml`), no como extra opcional al estilo
`anthropic`/`elevenlabs`/`openai`. La distinción es deliberada: esos
tres son SDKs de proveedores concretos, detrás de un `Provider`
intercambiable (ADR-0009) — instalarlos ata el proyecto a un vendor
específico, por eso son opcionales. `mutagen` no ata a ningún vendor:
es infraestructura genérica que el propio Core necesita para que
`SubtitleEngine` — parte del pipeline por defecto desde PR-018 —
funcione correctamente. Es la primera vez que `dependencies` deja de
estar vacío en este proyecto.

### Con fallback: el conteo de palabras no se elimina, se degrada a él

`measure_duration_seconds` devuelve `None` (no lanza) para cualquier
audio que no pueda interpretar — un contenedor no soportado, corrupto,
o bytes que no son audio en absoluto. Un `VoiceProvider` es código que
`velora` no controla (ADR-0009); un formato inusual de un proveedor no
debe abortar la generación completa de la Story. `SubtitleEngine.caption()`
conserva `words_per_minute` (por defecto `150.0`) exactamente como en
ADR-0021, pero ahora como **fallback**: solo se usa para una escena
cuya duración no pudo medirse, o que no tiene audio correspondiente en
absoluto. El resto de escenas de la misma `Story` se cronometran con su
duración real sin verse afectadas.

Esta degradación gradual, además de ser el comportamiento de producción
correcto, resulta también en que los tests existentes que usaban
`bytes` no reales como "audio" (`b"The city wakes."`, un patrón ya
establecido en toda la suite desde PR-012) siguen funcionando sin
cambios: `mutagen` no puede interpretarlos, y el fallback produce el
mismo resultado que antes. Los tests dedicados a la medición real usan
WAV válido, construido con el módulo estándar `wave` (duración exacta y
verificable, sin depender de codificar MP3 real).

### `StoryWorkflow`: el orden deja de ser incidental para ser una dependencia real

ADR-0019 y ADR-0021 documentaban que síntesis, ilustración, y
subtitulado eran independientes entre sí — el orden en `run()` seguía
el pipeline de ejemplo de `docs/VISION.md` por consistencia, no por
necesidad. Desde este PR, eso deja de ser cierto para el subtitulado:
`caption()` necesita el `StoryAudio` que `synthesize()` ya produjo, así
que el subtitulado debe ejecutarse después de la síntesis. Sigue sin
depender de la ilustración — ese orden entre ambos sigue siendo libre.

### CLI: `--words-per-minute` cambia de "el" ritmo a "el" ritmo de reserva

`velora create story` no requiere ninguna clave de API nueva.
`--words-per-minute` se conserva con el mismo nombre y valor por
defecto, pero su texto de ayuda se actualiza para reflejar su nuevo
rol: solo aplica a una escena cuya duración no pudo medirse desde el
audio generado.

## Consequences

- Los subtítulos que `velora create story` persiste ahora coinciden
  genuinamente con la duración del audio sintetizado, no con una
  estimación — la limitación que ADR-0021 dejó documentada
  explícitamente queda resuelta.
- `velora.engines.subtitle` gana una dependencia de tipo hacia
  `velora.engines.narration_audio` (por el tipo `StoryAudio`) — mismo
  patrón ya establecido por `velora.engines.narration_audio` y
  `velora.engines.scene_image`, que ya dependían de
  `velora.engines.story` únicamente por el tipo `Story`.
- Cualquier código existente que llamaba `SubtitleEngine.caption(story)`
  con un solo argumento deja de compilar: cambio incompatible
  deliberado, mismo criterio que ADR-0016/ADR-0019 ya aplicaron al
  extender la firma de `StoryWorkflow.run()`.
- `mutagen` es ahora una dependencia de instalación de `velora` en
  cualquier entorno, incluso quien no use `create story` en absoluto —
  aceptable dado su tamaño mínimo y ausencia de dependencias nativas
  compiladas.
- Un `VoiceProvider` futuro cuyo formato de audio `mutagen` no soporte
  seguirá funcionando correctamente vía el fallback, sin requerir
  ningún cambio en `SubtitleEngine` — la degradación es automática.
