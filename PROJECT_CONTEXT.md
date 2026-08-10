# PROJECT_CONTEXT

Este documento resume el estado actual de Velora. No duplica los ADR ni
`docs/VISION.md`; los referencia.

## Último PR

**PR-014 — Providers: `velora.providers.image`, respaldado por OpenAI
(DALL·E).**

## Milestone activa

**Providers** (tercer dominio horizontal: texto, voz, imagen). Próxima:
por decidir contigo — ver "Próximo paso".

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
- `velora.cli` — sin cambios en este PR: `create story` sigue
  requiriendo solo `VELORA_ANTHROPIC_API_KEY` y
  `VELORA_ELEVENLABS_API_KEY`; no conoce `velora.providers.image`.
- `velora.runtime` — sin cambios.
- `velora.configuration` — sin cambios funcionales; `VeloraSettings` no
  gana ninguna clave nueva en este PR (`OpenAIImageProvider` recibe su
  `api_key` directamente en el sitio de construcción, como cualquier
  Provider sin consumidor todavía en la CLI).
- `velora.logging` — sin cambios.
- `velora.services` (raíz), `velora.services.narration`,
  `velora.services.voice` — sin cambios.
- `velora.providers` (raíz) — sin cambios en la jerarquía de error
  compartida.
- `velora.providers.text_generation`, `velora.providers.voice` — sin
  cambios.
- `velora.providers.image` — **nuevo**: tercer dominio de Provider.
  `ImageProvider` (`generate(request: ImageRequest) -> ImageResult`),
  `ImageRequest` (`prompt: str`), `ImageResult` (`image: bytes`,
  `image_format: str`). Primera implementación real:
  `OpenAIImageProvider`, respaldada por la API de imágenes de OpenAI
  (DALL·E), mismo patrón que `AnthropicTextGenerationProvider` y
  `ElevenLabsVoiceProvider` (`LifecycleComponent`, extra opcional
  `velora[openai]`, traducción de excepciones a la jerarquía compartida
  de `velora.providers`). Sin consumidor todavía — ningún Service,
  Engine, o Workflow lo conoce.
- `velora.engines.story`, `velora.engines.narration_audio` — sin
  cambios.
- `velora.workflows.story` — sin cambios.

Ver `docs/architecture.md` para el detalle de cada símbolo.

## Componentes que NO existen todavía

Extensions. Tampoco `ImageService` (Service de capacidad para el
dominio imagen), ningún Engine que consuma `velora.providers.image`,
más Providers de imagen (Flux, Stable Diffusion), más dominios de
Provider (video, música, traducción), más Engines (Subtitle, Timeline,
Render, Publish), ni más Workflows que `StoryWorkflow`. Ningún
mecanismo para guardar a disco el audio que `StoryWorkflow` ya produce
— sigue pendiente, sin relación con este PR.

## Decisiones vigentes (ADR)

- **ADR-0001** a **ADR-0016** — ver PRs anteriores; sin cambios.
- **ADR-0017** — tercer dominio de Provider, `velora.providers.image`,
  respaldado por OpenAI (DALL·E) como primera implementación real.
  Mismo patrón exacto que ADR-0009 (`text_generation`) y ADR-0013
  (`voice`): subpaquete propio, contrato `Protocol` propio,
  `ImageRequest`/`ImageResult` mínimos, `LifecycleComponent` con
  `httpx.Client` inyectado explícitamente, extra opcional
  `velora[openai]` independiente de `anthropic` y `elevenlabs`. Mapeo
  de errores por clase de excepción (como `anthropic`, no por
  `status_code` como `elevenlabs`) porque así distingue sus propios
  errores el SDK de `openai`. Vinculante para cualquier dominio de
  Provider futuro: mismo patrón, mapeo de errores siempre investigado
  contra el SDK real elegido, nunca copiado mecánicamente.

## Criterios de aceptación vigentes

Desde un repositorio limpio:

```
git clone <repo>
uv sync
uv run velora
uv run pytest
```

El Core mantiene cobertura de pruebas ≥90%; PR-014 cierra con 100%.
`velora create story` no cambia su comportamiento ni sus requisitos en
este PR.

## Próximo paso

Con tres dominios de Provider ya reales (texto, voz, imagen) y uno de
ellos —imagen— todavía sin ningún consumidor, quedan varios caminos
razonables para `Genera PR-015` — no mutuamente excluyentes, pero
conviene decidir el orden:

1. **`ImageService`** — Service de capacidad para `image`, mismo patrón
   que `NarrationService` (ADR-0010) y `VoiceService` (ADR-0014):
   envuelve `ImageProvider` con la interfaz que un futuro Engine
   necesitará, antes de que exista ese Engine — mismo orden que ya
   siguió el dominio voz (Provider → Service → Engine).
2. **Persistir el audio a disco desde la CLI** — sigue pendiente desde
   el "Próximo paso" de PR-013; no se descartó, solo se pospuso al
   elegir el dominio horizontal.
3. **Seguir horizontal una vez más**: un cuarto dominio de Provider
   (video, música, traducción) antes de conectar verticalmente
   `image` — mantiene la disciplina de "un dominio a la vez" que ya
   rigió texto→voz→imagen.

Mi inclinación, si preguntas: opción 1. Es el mismo siguiente paso que
ya se tomó para voz (`ElevenLabsVoiceProvider` → `VoiceService` →
`NarrationAudioEngine`, PR-010→PR-011→PR-012) — mantener la misma
secuencia por dominio hace el patrón predecible antes de decidir cómo
`StoryWorkflow` (u otro Workflow) termina usando imágenes. Pero, a
diferencia de la decisión de este PR (que sí exigía elegir un dominio y
un proveedor concretos antes de escribir código), esta es de nuevo más
una cuestión de secuencia que de diseño, así que dímelo y sigo.
