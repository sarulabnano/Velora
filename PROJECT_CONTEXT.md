# PROJECT_CONTEXT

Este documento resume el estado actual de Velora. No duplica los ADR ni
`docs/VISION.md`; los referencia.

## Último PR

**PR-015 — Services: `ImageService`, capacidad delgada sobre
`ImageProvider`.**

## Milestone activa

**Services — capacidad, dominio imagen.** Tercer Service de capacidad
(`NarrationService`, `VoiceService`, `ImageService`), todos existentes
ya. Próxima: por decidir contigo — ver "Próximo paso".

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
  `VELORA_ELEVENLABS_API_KEY`; no conoce `ImageService`.
- `velora.runtime` — sin cambios.
- `velora.configuration` — sin cambios.
- `velora.logging` — sin cambios.
- `velora.services` (raíz) — sin cambios.
- `velora.services.narration`, `velora.services.voice` — sin cambios.
- `velora.services.image` — **nuevo**: tercer Service de capacidad.
  `ImageService.draw(prompt: str) -> ImageResult`, envolviendo un
  `ImageProvider` inyectado. Sin consumidor todavía — ningún Engine o
  Workflow lo conoce.
- `velora.providers` (raíz), `velora.providers.text_generation`,
  `velora.providers.voice`, `velora.providers.image` — sin cambios.
- `velora.engines.story`, `velora.engines.narration_audio` — sin
  cambios.
- `velora.workflows.story` — sin cambios.

Ver `docs/architecture.md` para el detalle de cada símbolo.

## Estado real del producto — qué se puede hacer hoy

Vale la pena resumirlo explícitamente, porque las piezas están
deliberadamente aisladas hasta que un Engine/Workflow las coordina:

- **Solo texto**: `StoryEngine` por sí solo. Funciona hoy, sin código
  nuevo.
- **Texto + audio**: `StoryWorkflow` completo, o `velora create story`
  desde la CLI (requiere ambas claves de API). Funciona hoy.
- **Texto + audio + imágenes**: **no existe como flujo integrado.**
  `ImageService`/`ImageProvider` existen y funcionan de forma aislada,
  pero nada en `StoryWorkflow` ni en la CLI los conoce — generar una
  imagen por escena hoy requeriría código propio, sin ninguna
  orquestación automática.

## Componentes que NO existen todavía

Extensions. Tampoco un Engine o Workflow que consuma `ImageService`
(el paso que conectaría texto+audio+imagen en un solo flujo), más
Providers de imagen (Flux, Stable Diffusion), más dominios de Provider
(video, música, traducción), más Engines (Subtitle, Timeline, Render,
Publish), ni más Workflows que `StoryWorkflow`. Ningún mecanismo para
guardar a disco el audio que `StoryWorkflow` ya produce — sigue
pendiente, sin relación con este PR.

## Decisiones vigentes (ADR)

- **ADR-0001** a **ADR-0017** — ver PRs anteriores; sin cambios.
- **ADR-0018** — `ImageService`, tercer Service de capacidad. Mismo
  patrón exacto que ADR-0010 (`NarrationService`) y ADR-0014
  (`VoiceService`): contrato delgado de un solo método
  (`draw(prompt: str) -> ImageResult`), reutiliza `ImageResult` sin
  envolverlo, validación mínima con `ValueError`, Provider inyectado
  nunca construido internamente. Nombrado `draw` en vez de `generate`
  únicamente para no colisionar léxicamente con
  `ImageProvider.generate()` en el mismo call stack — sin diferencia
  semántica. Vinculante para cualquier Service de capacidad futuro:
  mismo patrón, un verbo de dominio propio en vez de repetir el del
  Provider.

## Criterios de aceptación vigentes

Desde un repositorio limpio:

```
git clone <repo>
uv sync
uv run velora
uv run pytest
```

El Core mantiene cobertura de pruebas ≥90%; PR-015 cierra con 100%.
`velora create story` no cambia su comportamiento ni sus requisitos en
este PR.

## Próximo paso

Con los tres Services de capacidad ya reales (`NarrationService`,
`VoiceService`, `ImageService`) y ninguno de imagen conectado todavía a
ningún Engine o Workflow, quedan varios caminos razonables para
`Genera PR-016` — no mutuamente excluyentes, pero conviene decidir el
orden:

1. **Un Engine de imagen** (p. ej. `SceneImageEngine`) que, dada una
   `Story`, genere una imagen por escena vía `ImageService` — mismo
   patrón que `NarrationAudioEngine` ya estableció para audio
   (ADR-0015): recibe la `Story` ya construida, produce un tipo
   `StoryImages` (o como se decida llamarlo) con una imagen por escena.
   Es el paso que, exactamente igual que pasó con audio en PR-012,
   deja el nuevo dominio con un consumidor real por primera vez.
2. **Extender `StoryWorkflow` una tercera vez**, una vez exista el
   Engine de imagen, para que coordine los tres — mismo patrón que
   ADR-0016 ya estableció al coordinar los primeros dos; no tiene
   sentido antes de que exista el Engine del punto 1.
3. **Persistir el audio a disco desde la CLI** — sigue pendiente desde
   PR-013; no se descartó, solo se pospuso dos veces ya al elegir
   seguir horizontal.

Mi inclinación, si preguntas: opción 1. Es la misma secuencia que ya
demostró funcionar para voz (Provider → Service → Engine →
Workflow extendido), y es el paso que —por fin— le daría a
`ImageService` un consumidor real, cerrando el ciclo que dejó abierto
ADR-0018. Pero, igual que en decisiones anteriores de secuencia (no de
diseño concreto), dímelo y sigo.
