# ADR-0008: Dirección Services ↔ Providers, y diagrama de capas canónico

## Status

Accepted

## Context

Al incorporar `docs/VISION.md` (la visión de producto: Velora como
plataforma de automatización de producción audiovisual con IA) se
detectó una contradicción real con el diagrama de capas original del
AGENT.md.

AGENT.md original (`Applications → Workflows → Engines → Providers →
Services → Configuration → Logging → Runtime`): Services está **debajo**
de Providers → Providers depende de Services.

`docs/VISION.md` (`CLI → Runtime → Workflow Engine → Engines → Services
→ Providers → External APIs`): Services está **encima** de Providers →
Services depende de Providers. Textualmente: *"Narration Service...
puede usar GPT, Claude, Gemini... El Workflow nunca necesita saber
cuál usa"* — un Service de capacidad envuelve uno o más Providers.

Son direcciones opuestas del mismo par de capas. No es una ambigüedad
menor: cambia qué puede importar qué.

## Decision

Se adopta la dirección de `docs/VISION.md`: **Services depende de
Providers**, no al revés. Es la fuente más detallada y concreta sobre el
dominio real (Narration Service, Image Service como abstracciones de
capacidad sobre Providers intercambiables), y encaja con Dependency
Injection tal como la describe VISION.md: `OpenAIClient → ImageService →
Workflow` — el Provider se inyecta *hacia* el Service, no al revés.

Esto reproduce exactamente el patrón ya resuelto en ADR-0001 (roadmap de
construcción ≠ grafo de dependencias): el roadmap congelado sigue
construyendo **Services antes que Providers** (PR-005 antes que PR-006),
pero el grafo de dependencias dice que un Service de capacidad real
*necesita* un Provider para funcionar. Igual que Configuration definió
su contrato de error antes de que Logging existiera, PR-005 solo puede
definir **contratos** de Services de capacidad (si los hay) — nunca
implementaciones reales respaldadas por un Provider, porque ningún
Provider existe todavía.

### Dos categorías de Service

`docs/VISION.md` describe Services como *"capacidades del sistema, no
representan APIs"*. Eso cubre dos casos distintos, y esta ADR los nombra
explícitamente porque el roadmap los trata de forma distinta:

1. **Services de infraestructura** — no dependen de ningún Provider, son
   utilidades técnicas puras (`Clock`, `IdGenerator`, construidos en este
   mismo PR-005). Pueden construirse completos, reales y con
   implementación por defecto, hoy, sin esperar a Providers.
2. **Services de capacidad** — envuelven uno o más Providers
   intercambiables (`NarrationService`, `ImageService`, futuros). Su
   *contrato* podría definirse ahora, pero su implementación real no
   puede existir hasta que exista al menos un Provider real que la
   respalde (PR-006 en adelante). Definir el contrato sin ningún Provider
   real que lo satisfaga hoy sería exactamente el tipo de "código
   incompleto para uso futuro" que el manifiesto prohíbe — así que
   PR-005 no los incluye. Se construirán cuando su primer Provider real
   exista, no antes.

### Diagrama de capas canónico (vigente, integra AGENT.md + VISION.md)

```
Applications / Workflows
        │
        ▼
    Engines
        │
        ▼
    Services  ← (de capacidad: dependen de Providers)
        │
        ▼
    Providers
        │
        ▼
    Services  ← (de infraestructura: no dependen de Providers)
        │
        ▼
    Configuration
        │
        ▼
    Logging
        │
        ▼
    Runtime
```

"Services" no es una única posición en la cadena de dependencias — es
una etiqueta de rol (arquitecture.md original §9 style) que se aplica a
dos familias con dependencias distintas. Esto es inusual pero honesto:
refleja lo que `docs/VISION.md` describe, en vez de forzar una única
posición que no sería cierta para ambas familias.

## Consequences

- PR-005 se limita a Services de infraestructura (`Clock`,
  `IdGenerator`). No introduce ningún contrato de Service de capacidad
  todavía — evita construir una interfaz sin implementador real posible.
- PR-006 (Providers) queda con una responsabilidad más nítida: adaptar
  APIs externas (OpenAI, ElevenLabs, Flux, Runway, Suno, DeepL, etc. —
  ver `docs/VISION.md`) detrás de contratos tipados por dominio (IA de
  texto, voz, imagen, video, música, traducción).
- Los primeros Services de capacidad (probablemente `NarrationService`
  primero, dado que es el ejemplo con más Providers ya disponibles) se
  introducirán en un PR posterior a Providers, no en el PR-005 actual ni
  en el PR-006 de Providers mismo — mantiene cada PR enfocado en una sola
  capa.
- `docs/VISION.md` queda incorporado al repositorio como la fuente de
  verdad del dominio; futuras discrepancias entre él y el código
  construido se resuelven vía una ADR nueva, nunca editando VISION.md en
  silencio.
