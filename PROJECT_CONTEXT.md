# PROJECT_CONTEXT

Este documento resume el estado actual de Velora. No duplica los ADR ni
`docs/VISION.md`; los referencia.

## Último PR

**PR-010 — Providers: dominio `voice`, respaldado por ElevenLabs.**

## Milestone activa

**Providers** (segundo dominio completado: `voice`, sobre
`ElevenLabsVoiceProvider`). Próxima: por decidir contigo — ver "Próximo
paso".

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
- `velora.cli` — sin cambios en este PR.
- `velora.runtime` — sin cambios funcionales en este PR.
- `velora.configuration` — sin cambios en este PR.
- `velora.logging` — sin cambios funcionales en este PR.
- `velora.services` (raíz) — Services de infraestructura, sin cambios.
- `velora.services.narration` — `NarrationService`, sin cambios.
- `velora.providers` (raíz) — sin cambios.
- `velora.providers.text_generation` — sin cambios.
- `velora.providers.voice` — **nuevo**: `VoiceProvider`
  (`synthesize(request: SpeechRequest) -> SpeechResult`),
  `SpeechRequest` (`text`), `SpeechResult` (`audio: bytes`,
  `audio_format: str`), `ElevenLabsVoiceProvider` (primera
  implementación real, requiere el extra `velora[elevenlabs]`). Sin
  consumidor todavía dentro del código base.
- `velora.engines.story` — sin cambios.
- `velora.workflows.story` — sin cambios.

Ver `docs/architecture.md` para el detalle de cada símbolo.

## Componentes que NO existen todavía

Extensions. Tampoco Providers de imagen, video, música o traducción,
más Services de capacidad (incluido un `VoiceService` que consuma
`velora.providers.voice`), más Engines (Subtitle, Timeline, Render,
Publish), ni más Workflows que `StoryWorkflow`.

## Decisiones vigentes (ADR)

- **ADR-0001** a **ADR-0012** — ver PRs anteriores; sin cambios.
- **ADR-0013** — `velora.providers.voice`, segundo dominio de Provider,
  mismo patrón que ADR-0009 estableció para `text_generation`.
  `SpeechRequest` deliberadamente mínimo (un solo campo, `text`); la
  voz se elige en el Provider (constructor), no en el request, hasta
  que un llamador real necesite variarla entre llamadas.
  `ElevenLabsVoiceProvider` inyecta su propio `httpx.Client` en el SDK
  en vez de depender de su estructura interna para cerrarlo. El SDK de
  `elevenlabs` no distingue clases de excepción por código HTTP más
  allá de 422 — el mapeo de errores inspecciona `status_code`
  explícitamente en vez de inventar tipos que el SDK no distingue.
  Vinculante para todo Provider futuro: investigar el mapeo de errores
  del SDK real elegido, nunca copiarlo mecánicamente de otro dominio.

## Criterios de aceptación vigentes

Desde un repositorio limpio:

```
git clone <repo>
uv sync
uv run velora
uv run pytest
```

Sin cambios respecto a PR-009. El Core mantiene cobertura de pruebas
≥90%; PR-010 cierra con 100%. `velora.providers.voice` no tiene
consumidor en la CLI todavía — no hay comando `velora create ...` nuevo
en este PR.

## Próximo paso

Con `velora.providers.voice` funcionando (sin consumidor todavía), hay
varios caminos razonables — necesito tu decisión antes de `Genera
PR-011`:

1. **`VoiceService`** (`velora.services.voice`), sobre
   `VoiceProvider` — capacidad de "hablar", envolviendo un
   `VoiceProvider` inyectado. Mismo patrón que `NarrationService`
   (ADR-0010).
2. **Segundo Engine, sobre voz**: por ejemplo, extender
   `StoryWorkflow`/un nuevo Engine para que la narración de una `Story`
   también se sintetice a audio — la primera vez que `StoryWorkflow`
   coordinaría más de un Engine real.
3. **Tercer dominio de Provider** (imagen) antes de construir sobre
   `voice` — sigue ampliando cobertura horizontal.

Mi inclinación, si preguntas: opción 1 (`VoiceService`) — es el paso
intermedio que ADR-0010 ya demostró que vale la pena dar antes de un
Engine: una capa delgada que desbloquea a quien la use después
(`StoryWorkflow`, un futuro `NarrationAudioEngine`) sin comprometerse
todavía a una decisión de orquestación mayor. Pero es tu llamada.
