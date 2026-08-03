# PROJECT_CONTEXT

Este documento resume el estado actual de Velora. No duplica los ADR ni
`docs/VISION.md`; los referencia.

## Último PR

**PR-006 — Providers (dominio text_generation).**

## Milestone activa

**Providers** (primer dominio completado: `text_generation`, respaldado
por Anthropic). Próxima: un segundo dominio de Providers, o **Engines**
(PR-007) — el roadmap fija el orden de fases, no cuántos PRs ocupa cada
una; añadir más dominios de Providers antes de avanzar a Engines es una
decisión abierta, a confirmar contigo.

## Roadmap (congelado, no modificable)

```
Foundation → Runtime → Configuration → Logging → Services →
Providers → Engines → Workflows → Extensions
```

## Documento de visión

`docs/VISION.md` — visión de producto. Incorporado en PR-005.
Discrepancias con lo construido se resuelven vía ADR (ADR-0008 fue la
primera; ADR-0009 continúa aplicando sus definiciones a Providers).

## Componentes que existen hoy

- `velora` — paquete raíz, expone `__version__`.
- `velora.cli` — composition root: Configuration → Logging → Runtime
  (con Services inyectado). Sin cambios en este PR — Providers no tiene
  todavía ningún consumidor en el CLI (correcto: no hay Service de
  capacidad que lo use aún).
- `velora.runtime` — núcleo estable, sin cambios funcionales en este PR.
- `velora.configuration`, `velora.logging` — sin cambios en este PR.
- `velora.services` — Services de infraestructura (`Clock`,
  `IdGenerator`), sin cambios en este PR.
- `velora.providers` — jerarquía de error compartida
  (`VeloraProviderError` y subclases).
- `velora.providers.text_generation` — primer dominio de Provider:
  `TextGenerationProvider` (contrato), `Message`/`Role`/
  `TextGenerationRequest`/`TextGenerationResult` (tipos), y
  `AnthropicTextGenerationProvider` (implementación real, requiere el
  extra opcional `velora[anthropic]`, primer implementador no trivial de
  `LifecycleComponent`).

Ver `docs/architecture.md` para el detalle de cada símbolo.

## Componentes que NO existen todavía

Engines, Workflows, Extensions. Tampoco Providers de voz, imagen, video,
música o traducción, ni ningún Service de capacidad (`NarrationService`,
etc. — ahora desbloqueado por este PR, ver ADR-0008).

## Decisiones vigentes (ADR)

- **ADR-0001** a **ADR-0007** — ver PRs anteriores; sin cambios.
- **ADR-0008** — Resuelve `Providers ↔ Services`: Services de capacidad
  dependen de Providers. Dos categorías de Service. Diagrama de capas
  canónico.
- **ADR-0009** — Contrato por dominio de Provider (no un `Provider`
  genérico); alcance síncrono y sin streaming, deliberado; dependencias
  de SDK vía `[project.optional-dependencies]`, nunca obligatorias;
  criterio para cuándo un Provider implementa `LifecycleComponent`
  ("¿hay un recurso real?"). Vinculante para todo Provider futuro, en
  cualquier dominio.

## Criterios de aceptación vigentes

Desde un repositorio limpio:

```
git clone <repo>
uv sync
uv run velora
uv run pytest
```

`uv sync` instala también `anthropic` (grupo `dev`, y extra opcional
`anthropic` para uso real de `AnthropicTextGenerationProvider`) — no
supone llamadas de red ni requiere credenciales para pasar los tests:
el cliente del SDK se sustituye por dobles de prueba en toda la suite.

El Core (`velora`, `velora.cli`, `velora.runtime`, `velora.configuration`,
`velora.logging`, `velora.services`, `velora.providers`) mantiene
cobertura de pruebas ≥90%; PR-006 cierra con 100%.

## Próximo paso

Dos caminos igualmente válidos, a decidir contigo:

1. **Más dominios de Providers** (voz, imagen, video, música,
   traducción) antes de avanzar a Engines — completa la capa Providers
   con más cobertura de `docs/VISION.md` antes de construir lo que la
   orquesta.
2. **PR-007 — Engines**, empezando a orquestar `TextGenerationProvider`
   (el único dominio disponible) en una lógica de negocio real (p. ej.
   un "Story Engine" simple). Requiere decidir primero si Engines
   depende directamente de Providers o solo a través de un Service de
   capacidad (`NarrationService`) — el diagrama canónico (ADR-0008) dice
   que Engines está por encima de Services, así que Engines debería
   depender del Service, no del Provider directamente; eso implicaría
   construir `NarrationService` (el primer Service de capacidad) como
   parte de, o inmediatamente antes de, PR-007.
