# ADR-0010: `NarrationService` antes de Engines; diseño deliberadamente delgado

## Status

Accepted

## Context

Tras PR-006 (Providers, dominio `text_generation`), quedaban dos caminos
igualmente razonables: más dominios de Providers, o empezar Engines. El
diagrama de capas canónico (ADR-0008) dice que Engines depende de
Services de capacidad, no de Providers directamente. Empezar Engines
ahora habría forzado una de dos cosas: violar esa dirección (Engine
importando un Provider directamente), o bloquear Engines hasta que
existiera al menos un Service de capacidad. Se eligió resolver el
bloqueo: construir el primer Service de capacidad ahora.

`docs/VISION.md` usa `Narration Service` como su ejemplo canónico de
Service de capacidad ("puede usar GPT, Claude, Gemini... sin cambiar el
resto del proyecto"), así que es la elección obvia para ser el primero.

## Decision

### Ubicación: subpaquete de `velora.services`, no un paquete nuevo

`velora.services.narration`, no `velora.capabilities.narration` ni
similar. ADR-0008 ya estableció que "Services de infraestructura" y
"Services de capacidad" son dos categorías del mismo concepto
(`docs/VISION.md`: "representan capacidades del sistema"), con distinta
posición en el grafo de dependencias — no dos conceptos distintos que
merezcan paquetes de nivel superior separados. Se mantiene fuera de la
raíz de `velora.services` (que sigue exportando solo `Clock`/
`IdGenerator`) para que importar la infraestructura nunca arrastre
`velora.providers` para quien no lo necesita.

### Contrato deliberadamente delgado

`NarrationService.narrate(instructions: str, *, max_tokens: int = 1024)
-> TextGenerationResult` no decide estructura narrativa, tono más allá
de un system prompt genérico, ni duración. Decidir *qué* narrar y cómo
se divide un guion en escenas es lógica de negocio que pertenece a un
Engine futuro (`docs/VISION.md`: "Story Engine construye la historia").
Este Service solo sabe convertir instrucciones en texto de narración.
Ampliar su superficie (tono estructurado, longitud objetivo, idioma)
es una extensión aditiva futura si un Engine real la necesita — no se
anticipa aquí sin ese consumidor.

### Reutiliza `TextGenerationResult`, no un tipo nuevo

`NarrationService.narrate()` devuelve `TextGenerationResult`
directamente, sin envolverlo en un `NarrationResult` nuevo.
`TextGenerationResult` ya es provider-agnóstico (vive en
`velora.providers.text_generation`, no en ningún Provider concreto), así
que envolverlo de nuevo no añadiría independencia del proveedor — solo
ceremonia. Si en el futuro `NarrationService` necesita devolver algo que
`TextGenerationResult` no modela, ese es el momento de introducir un tipo
propio, no antes (Regla de oro del manifiesto).

### Validación mínima con excepción estándar, no una jerarquía nueva

`narrate()` rechaza instrucciones vacías con un `ValueError` simple, no
con una nueva jerarquía `VeloraServiceError`. Es la única precondición
que este Service verifica; los fallos reales de negocio (autenticación,
límite de tasa, conexión) ya están tipados en `velora.providers`. Crear
una jerarquía de errores para una sola comprobación de precondición
sería infraestructura sin más de un llamador — exactamente lo que el
manifiesto pide evitar. Si un futuro Service de capacidad acumula varias
condiciones de fallo propias, esa es la señal para introducir su propia
jerarquía tipada, siguiendo el patrón ya establecido
(`VeloraConfigurationError`, `VeloraRuntimeError`, `VeloraProviderError`).

## Consequences

- `NarrationService` es la primera pieza que un futuro Engine puede
  depender de forma legítima sin romper el diagrama canónico de
  ADR-0008: `Engine → NarrationService → TextGenerationProvider →
  anthropic`. El Engine nunca ve `velora.providers` ni `anthropic`.
- Cualquier Service de capacidad futuro (`ImageService`, etc.) sigue el
  mismo patrón: subpaquete de `velora.services`, contrato delgado,
  reutiliza los tipos de resultado de su dominio de Provider en vez de
  envolverlos, jerarquía de error propia solo cuando haya más de una
  condición de fallo real que lo justifique.
- El siguiente paso natural es PR-007: el primer Engine real (candidato:
  un Story Engine mínimo, o directamente exponer `NarrationService` a
  través de un Workflow simple) — a decidir explícitamente antes de
  empezar, dado que "Engines ejecutan lógica compleja" es, de los tres
  documentos (AGENT.md, architecture.md, VISION.md), el concepto menos
  especificado hasta ahora.
