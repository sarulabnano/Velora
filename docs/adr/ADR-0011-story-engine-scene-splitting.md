# ADR-0011: `StoryEngine` — división de escenas determinista, sin control de conteo

## Status

Accepted

## Context

`StoryEngine` es el primer Engine (`docs/VISION.md`: "Los Engines
ejecutan lógica compleja... Story Engine construye la historia").
Ninguno de los tres documentos de referencia (AGENT.md,
`architecture.md` original, `docs/VISION.md`) especifica *cómo* debe
dividirse una narración en escenas, ni si debe soportarse un número
objetivo de escenas. Había que decidir esto desde cero, con el riesgo de
inventar de más.

## Decision

### División por párrafos, no por delimitador pedido al modelo

`StoryEngine` divide el texto devuelto por `NarrationService` en
párrafos (líneas en blanco), con una expresión regular determinista —
no le pide al modelo que use un delimitador especial (p. ej. `"---"`)
para luego parsear ese formato. Un Provider real puede no seguir
instrucciones de formato de forma perfectamente consistente; depender de
eso para algo tan estructural como los límites de escena sería frágil de
una forma que solo se manifestaría en producción, no en los tests (que
usan un Provider falso perfectamente obediente). Partir por párrafos no
depende de que el modelo "obedezca" nada.

### Sin control de número de escenas

`build_story()` no acepta ni garantiza un `scene_count`. Fusionar o
dividir párrafos para forzar un número exacto es un problema de diseño
real y separado (¿se fusionan los más cortos? ¿se trunca el sobrante?)
sin ninguna especificación concreta todavía. Es mejor no construirlo que
construirlo adivinando. Es una extensión aditiva futura de `build_story`
si un caso de uso real la necesita.

### Historia vacía es un estado válido, no un error

Si la narración generada queda en blanco tras el recorte, `Story` se
construye con `scenes=()` en vez de lanzar una excepción. No hay
evidencia de que una historia vacía sea necesariamente un error de uso —
podría ser una respuesta legítima del Provider ante ciertas
instrucciones; corresponde a quien consuma `Story` decidir qué hacer con
ella, no a `StoryEngine` inventar que es un fallo.

### Sin jerarquía de error propia todavía

`build_story()` usa `ValueError` para su única precondición (`topic`
vacío) — mismo patrón que `NarrationService` (ADR-0010). `velora.engines`
(paquete raíz) no define ninguna jerarquía de error compartida: ningún
segundo Engine existe todavía que revele qué tendría sentido compartir
entre engines. Se introducirá cuando un segundo Engine la necesite
genuinamente, no antes.

## Consequences

- `StoryEngine` depende de `NarrationService`, nunca de
  `TextGenerationProvider` ni de `anthropic` directamente — respeta el
  diagrama canónico de ADR-0008 (Engines depende de Services de
  capacidad, no de Providers).
- Los tests de `StoryEngine` usan un `NarrationService` real con un
  `TextGenerationProvider` falso — ejercitan la integración real entre
  ambos, no un doble de `NarrationService` — dejando como única frontera
  simulada la llamada externa real.
- Cualquier Engine futuro que también necesite "dividir texto en
  unidades" (p. ej. un Subtitle Engine dividiendo en líneas de
  subtítulo) decide su propio criterio de división; no se extrae una
  utilidad compartida de `_split_into_scenes` hasta que un segundo
  consumidor real la necesite de la misma forma.
