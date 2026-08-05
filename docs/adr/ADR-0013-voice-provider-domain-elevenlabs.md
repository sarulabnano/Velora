# ADR-0013: `velora.providers.voice`, respaldado por ElevenLabs

## Status

Accepted

## Context

Tras PR-009 (Workflows), `PROJECT_CONTEXT.md` dejaba tres caminos: un
segundo Engine, un segundo Workflow, o un segundo dominio de
Providers/Services. Se eligió un segundo dominio: amplía cobertura
horizontal y es lo que más directamente desbloquea un segundo Engine
real después — construir un segundo Engine o un segundo Workflow antes
de tener con qué llenarlos de contenido genuinamente distinto (más allá
de narración de texto) habría sido prematuro.

`docs/VISION.md` lista los pasos del Workflow de ejemplo ("Crear
documental") en este orden: investigar → escribir → dividir escenas →
**generar voz** → generar imágenes → construir timeline → renderizar →
publicar. `StoryEngine`/`StoryWorkflow` ya cubren "escribir" y "dividir
escenas"; el paso siguiente en ese pipeline documentado es voz, no
imagen — es también el dominio que más directamente extiende lo que
`StoryWorkflow` ya produce (convertir la narración de una `Story` en
audio real), en vez de abrir un frente nuevo sin conexión con lo
existente.

`docs/VISION.md` lista como Providers de voz posibles: Voicebox,
ElevenLabs, XTTS, Piper. Se eligió **ElevenLabs** como primera
implementación real: tiene un SDK oficial en PyPI (`elevenlabs`, sin
relación con el paquete `anthropic` ya usado), API de texto-a-voz
síncrona simple, y voces predefinidas disponibles en todos los planes
(sin necesidad de clonar o entrenar una voz para tener algo funcional
desde el primer PR).

## Decision

### Dominio propio, mismo patrón que `text_generation` (ADR-0009)

`velora.providers.voice`, no una extensión de `velora.providers.text_
generation` ni un `Provider` genérico — mismo razonamiento exacto que
ADR-0009 ya estableció: cada dominio de Provider es su propio
subpaquete con su propio contrato.

- **`VoiceProvider`** (`_protocol.py`) — `synthesize(request:
  SpeechRequest) -> SpeechResult`. Síncrono, sin streaming — misma
  decisión que ADR-0009 tomó para `TextGenerationProvider`, por la
  misma razón: el resto del sistema (`Services`, `Engines`, `Workflows`)
  no tiene todavía ningún consumidor que necesite streaming.
- **`SpeechRequest`** (`_types.py`) — un único campo, `text: str`.
  Deliberadamente mínimo: es lo único que varía para el único llamador
  real de hoy. La elección de voz vive en el Provider (`voice_id` en su
  constructor, mismo patrón que `model` en
  `AnthropicTextGenerationProvider`), no en el request — no hay todavía
  ningún llamador real que necesite cambiar de voz entre llamadas
  sucesivas a un mismo Provider; cuando lo haya, ese es el momento de
  mover la elección de voz al request (Regla de oro).
- **`SpeechResult`** (`_types.py`) — `audio: bytes`, `audio_format:
  str`. `audio_format` es siempre `"mp3"` hoy (lo único que produce la
  única implementación real) — no un enum: un enum de un solo miembro no
  se justifica todavía (mismo razonamiento que ya evitó introducir una
  jerarquía de error propia para `NarrationService`/`StoryEngine` con
  una sola precondición).
- **`ElevenLabsVoiceProvider`** (`_elevenlabs.py`) — primera
  implementación real. Mismo patrón exacto que
  `AnthropicTextGenerationProvider`: implementa
  `~velora.runtime.LifecycleComponent` (`start()` crea el cliente HTTP,
  `stop()` lo cierra); traduce las excepciones propias del SDK de
  ElevenLabs a la jerarquía compartida de `velora.providers`; requiere
  el extra opcional `velora[elevenlabs]`, con el mismo `ImportError`
  guiado si falta que ya usa `_anthropic.py`.

### Mapeo de errores: por `status_code`, no por clase de excepción

A diferencia del SDK de `anthropic` (que expone clases de excepción
específicas — `AuthenticationError`, `RateLimitError`,
`APIConnectionError`) el SDK de `elevenlabs` solo distingue una clase
propia para 422 (`UnprocessableEntityError`); cualquier otro código de
error HTTP (401, 403, 429, 5xx...) llega como la misma
`elevenlabs.core.ApiError` genérica, distinguible solo por su atributo
`status_code`. `ElevenLabsVoiceProvider.synthesize()` inspecciona ese
atributo explícitamente (`401` → `ProviderAuthenticationError`, `429` →
`ProviderRateLimitError`, cualquier otro → `ProviderRequestError`) en
vez de inventar tipos de excepción que el SDK no distingue. Fallos de
conexión (DNS, timeout, conexión rechazada) no los envuelve el SDK en
absoluto — se propaga `httpx.HTTPError` directamente desde `httpx`, la
librería HTTP subyacente — así que `synthesize()` también captura
`httpx.HTTPError` y lo traduce a `ProviderConnectionError`. Este mapeo
es específico de cómo está construido el SDK de ElevenLabs hoy, no un
patrón que se pueda copiar mecánicamente a un tercer dominio de
Provider sin volver a inspeccionar su propio SDK.

### Gestión del cliente HTTP: `httpx.Client` inyectado explícitamente

`ElevenLabs` (la clase del SDK) acepta un `httpx_client` propio en su
constructor. `start()` construye su propio `httpx.Client()` y se lo pasa
explícitamente, en vez de dejar que el SDK construya uno internamente y
alcanzar su atributo privado para cerrarlo en `stop()` — evita depender
de la estructura interna no documentada del SDK para el cierre limpio
del pool de conexiones.

### `pyproject.toml`: extra `elevenlabs`, independiente de `anthropic`

`[project.optional-dependencies] elevenlabs = ["elevenlabs>=2.60,<3"]`
— extra propio, no agrupado con `anthropic`: quien solo necesite
`text_generation` no debe instalar el SDK de ElevenLabs, y viceversa
(mismo principio que ya aplica ADR-0009 a `anthropic`). Añadido también
al grupo `dev` (junto a `anthropic`), para que la suite de tests y
`mypy` puedan ejercitar `ElevenLabsVoiceProvider` de verdad.

## Consequences

- `velora.providers.voice` no importa `velora.services` ni
  `velora.engines`/`velora.workflows` en ningún punto — solo
  `velora.providers` (jerarquía de error) y `velora.runtime` (solo para
  `LifecycleComponent`), exactamente el mismo diagrama de dependencias
  que ya sigue `velora.providers.text_generation`.
- Ningún Service, Engine o Workflow existente cambia: `NarrationService`,
  `StoryEngine`, `StoryWorkflow` no saben que `voice` existe. Un futuro
  `VoiceService`/`Subtitle Engine`/segundo paso de `StoryWorkflow` los
  consumirá cuando exista un llamador real — no antes.
- Un tercer dominio de Provider futuro (imagen, video, música,
  traducción) sigue el mismo patrón: subpaquete propio bajo
  `velora.providers`, contrato (`Protocol`) propio, tipos de
  request/result propios y mínimos, mapeo de errores propio investigado
  contra el SDK real elegido — nunca copiado mecánicamente de
  `text_generation` o `voice` sin verificar cómo ese SDK concreto
  distingue sus propios errores.
