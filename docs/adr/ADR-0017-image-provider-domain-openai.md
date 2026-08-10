# ADR-0017: `velora.providers.image`, respaldado por OpenAI (DALL·E)

## Status

Accepted

## Context

Tras PR-013 (`StoryWorkflow` coordinando ya sus dos Engines,
ADR-0016), `PROJECT_CONTEXT.md` dejaba dos caminos para PR-014:
persistir a disco el audio que `StoryWorkflow` ya produce, o seguir
horizontal con un tercer dominio de Provider/Service. Se confirmó
seguir horizontal — mismo tipo de decisión que ADR-0013 ya tomó entre
PR-009 y PR-010 (segundo dominio de Provider en vez de un segundo
Engine o Workflow), aplicada ahora una capa de dominio más allá.

`docs/VISION.md` lista los Providers de cada dominio en este orden:
texto/IA, **Voz**, **Imágenes**, video, música, traducción — el mismo
orden en que `velora.providers.text_generation` (PR-006) y
`velora.providers.voice` (PR-010, ADR-0013) ya se construyeron.
Imágenes es también el paso que sigue a "generar voz" en el pipeline
de ejemplo de `docs/VISION.md` ("Crear documental": investigar →
escribir → dividir escenas → generar voz → **generar imágenes** →
construir timeline → renderizar → publicar) — el mismo criterio de
"seguir el pipeline documentado, no abrir un frente sin conexión" que
ADR-0013 ya aplicó para elegir voz sobre imagen en su momento.

Para el Provider concreto, `docs/VISION.md` lista: Flux, Stable
Diffusion, MidJourney (sin API pública) y DALL·E. Se pidió el más
simple/estable de la lista. Se eligió **DALL·E, vía el SDK oficial
`openai`**: es el único con un SDK oficial de Python cuya forma
—clases de excepción específicas por categoría
(`AuthenticationError`, `RateLimitError`, `APIConnectionError`,
`APIStatusError`)— es prácticamente idéntica a la de `anthropic`, ya
integrado en el proyecto desde PR-006 (ADR-0009); Flux y Stable
Diffusion, por contraste, se ofrecen mayormente vía SDKs de terceros
(Replicate, fal.ai, Stability AI) sin una convención de errores tan
uniforme entre sí.

## Decision

### Dominio propio, mismo patrón que `text_generation` y `voice`

`velora.providers.image`, no una extensión de ningún dominio
existente ni un `Provider` genérico — mismo razonamiento exacto que
ADR-0009 y ADR-0013 ya establecieron: cada dominio de Provider es su
propio subpaquete con su propio contrato.

- **`ImageProvider`** (`_protocol.py`) — `generate(request:
  ImageRequest) -> ImageResult`. Síncrono, sin streaming — misma
  decisión que ADR-0009 tomó para `TextGenerationProvider` y ADR-0013
  para `VoiceProvider`, por la misma razón: ningún consumidor real
  necesita streaming todavía.
- **`ImageRequest`** (`_types.py`) — un único campo, `prompt: str`.
  Deliberadamente mínimo, mismo criterio que `SpeechRequest` (ADR-0013):
  es lo único que varía para el único llamador real de hoy (que, de
  momento, no existe — ver "Consequences"). Modelo, tamaño y calidad
  viven en el Provider (constructor), no en el request, hasta que un
  llamador real necesite variarlos entre llamadas sucesivas (Regla de
  oro).
- **`ImageResult`** (`_types.py`) — `image: bytes`, `image_format: str`.
  `image_format` es siempre `"png"` hoy (lo único que produce
  `response_format="b64_json"` en la API de OpenAI) — no un enum, mismo
  razonamiento que `SpeechResult.audio_format` (ADR-0013).
- **`OpenAIImageProvider`** (`_openai.py`) — primera implementación
  real. Mismo patrón exacto que `AnthropicTextGenerationProvider` y
  `ElevenLabsVoiceProvider`: implementa
  `~velora.runtime.LifecycleComponent` (`start()` crea el cliente HTTP
  y el cliente del SDK, `stop()` los cierra); traduce las excepciones
  propias del SDK a la jerarquía compartida de `velora.providers`;
  requiere el extra opcional `velora[openai]`, con el mismo
  `ImportError` guiado si falta que ya usan `_anthropic.py` y
  `_elevenlabs.py`.

### Mapeo de errores: por clase de excepción, igual que `anthropic`

A diferencia del SDK de `elevenlabs` (que distingue errores sobre todo
por `status_code`, ADR-0013), el SDK de `openai` expone clases de
excepción específicas por categoría — `AuthenticationError`,
`RateLimitError`, `APIConnectionError`, y `APIStatusError` como base
genérica (de la que heredan, entre otras, `BadRequestError`) — con
firmas de constructor (`message`, `response`, `body`) idénticas a las
de `anthropic`. `OpenAIImageProvider.generate()` captura cada una por
tipo, en el mismo orden y con el mismo mapeo 1:1 que
`AnthropicTextGenerationProvider.generate()` ya usa. Este mapeo es
específico de cómo está construido el SDK de OpenAI hoy — que resulte
casi idéntico al de `anthropic` es una coincidencia entre dos SDKs
similares, no una regla general: ADR-0013 ya advirtió que ningún mapeo
de errores se copia mecánicamente a un dominio nuevo sin volver a
inspeccionar su propio SDK, y aquí se hizo esa inspección
(`docs/adr` no asume, verifica).

### Gestión del cliente HTTP: `httpx.Client` inyectado explícitamente

`OpenAI` (la clase del SDK) acepta un `http_client` propio en su
constructor — misma forma que `ElevenLabs` (ADR-0013). `start()`
construye su propio `httpx.Client()` y se lo pasa explícitamente, por
el mismo motivo: evita depender de la estructura interna no
documentada del SDK para el cierre limpio del pool de conexiones.

### Formato de respuesta: `response_format="b64_json"`, decodificado a `bytes`

La API de imágenes de OpenAI puede devolver una URL temporal o el
`b64_json` de la imagen directamente. Se eligió `b64_json`: mantiene
`ImageResult.image: bytes` como el mismo tipo de dato que
`SpeechResult.audio: bytes` ya usa — el llamador nunca necesita hacer
una segunda petición HTTP para obtener el contenido real, ni depender
de que una URL temporal siga viva quien sea que consuma el resultado
después. `generate()` decodifica el `b64_json` con `base64.b64decode`
antes de devolverlo.

### `pyproject.toml`: extra `openai`, independiente de `anthropic` y `elevenlabs`

`[project.optional-dependencies] openai = ["openai>=1.60,<3"]` — extra
propio, no agrupado con los otros dos: quien no use generación de
imágenes no debe instalar el SDK de OpenAI, y viceversa (mismo
principio que ADR-0009 y ADR-0013 ya aplicaron). Añadido también al
grupo `dev`, para que la suite de tests y `mypy` puedan ejercitar
`OpenAIImageProvider` de verdad.

## Consequences

- `velora.providers.image` no importa `velora.services` ni
  `velora.engines`/`velora.workflows` en ningún punto — solo
  `velora.providers` (jerarquía de error) y `velora.runtime` (solo para
  `LifecycleComponent`), exactamente el mismo diagrama de dependencias
  que ya siguen `velora.providers.text_generation` y
  `velora.providers.voice`.
- Ningún Service, Engine o Workflow existente cambia:
  `NarrationService`, `VoiceService`, `StoryEngine`,
  `NarrationAudioEngine`, `StoryWorkflow` no saben que `image` existe.
  Un futuro `ImageService`/`ImageEngine`/tercer paso de un Workflow lo
  consumirá cuando exista un llamador real — no antes, mismo principio
  que ya dejó `ElevenLabsVoiceProvider` sin consumidor entre PR-010 y
  PR-012.
- `velora create story` no cambia: no requiere `VELORA_OPENAI_API_KEY`
  ni construye `OpenAIImageProvider` — este PR es horizontal
  (Providers), no verticalmente conectado a ningún Engine o Workflow
  todavía.
- Un cuarto dominio de Provider futuro (video, música, traducción)
  sigue el mismo patrón: subpaquete propio bajo `velora.providers`,
  contrato (`Protocol`) propio, tipos de request/result propios y
  mínimos, mapeo de errores propio investigado contra el SDK real
  elegido — nunca copiado mecánicamente de `text_generation`, `voice`,
  o `image` sin verificar cómo ese SDK concreto distingue sus propios
  errores.
