# ADR-0004: Modelo de eventos del Runtime y política de fallo de listeners

## Status

Accepted

## Context

`architecture.md` §7 exige que el Runtime nunca escriba logs directamente
— "El Runtime emite eventos. El Logging decide cómo registrarlos." Esto
requiere un contrato de evento y un contrato de listener, disponibles
desde PR-002, aunque Logging (el primer consumidor real) no se construya
hasta una fase posterior. Dos decisiones de diseño no estaban resueltas:
la forma del tipo `RuntimeEvent`, y qué hace el Runtime si un listener
lanza una excepción al recibir un evento.

## Decision

### Forma del evento: dataclass plano + enum, no jerarquía de clases

`RuntimeEvent` es un único `dataclass(frozen=True, slots=True)` con tres
campos (`kind: RuntimeEventKind`, `component_name: str | None`,
`error: BaseException | None`). Se descartó una jerarquía de clases (una
subclase por tipo de evento, p. ej. `ComponentStartedEvent`,
`FatalErrorEvent`) por lo siguiente:

- **Estabilidad del listener frente a nuevos eventos.** Con un enum,
  añadir un tipo de evento nuevo es añadir un miembro — un listener
  existente que hace `match event.kind:` sigue compilando y funcionando
  sin cambios, simplemente sin una rama para el caso nuevo. Con una
  jerarquía de clases, un listener con `isinstance` en cascada no se
  rompe, pero cualquier código que dependa de una unión cerrada de tipos
  (`Union[EventA, EventB, ...]`) sí se rompe cada vez que se añade un
  evento — exactamente el tipo de fragilidad que "Stable Core" busca
  evitar.
- **Regla de oro del manifiesto:** "si existe una solución más simple con
  la misma calidad, esa es la correcta". Un solo dataclass es más simple
  de mantener, testear y documentar que N subclases, sin pérdida de
  información: los tres campos cubren todos los casos actuales.

### Excepciones de listeners no se capturan

`Runtime._emit` llama a cada listener sin `try/except`. Si un listener
lanza, la excepción interrumpe inmediatamente `start()` o `stop()`.

Se consideró la alternativa de capturar y aislar fallos de listeners
(para que un listener de logging roto no pudiera tumbar el arranque de
toda la aplicación). Se descartó porque:

- Es "magia oculta": un listener que falla en silencio es exactamente el
  tipo de comportamiento implícito que el manifiesto prohíbe ("No Hidden
  Magic").
- El contrato `RuntimeEventListener` ya documenta que un listener "no
  debe lanzar en operación normal". Si lo hace, es un defecto del
  listener, y Fail Fast dicta que un defecto se manifieste de inmediato y
  de forma ruidosa, no que quede enterrado.

## Consequences

- Cuando exista Logging (fase futura) y lo implemente como
  `RuntimeEventListener`, su implementación debe garantizar que
  `on_runtime_event` no lance excepciones por causas esperables (un
  backend de logging caído, por ejemplo, debe degradarse internamente,
  no propagar). Esta responsabilidad recae en Logging, no en el Runtime.
- `RuntimeEvent` es apto para serialización estructurada (todos sus
  campos son primitivos o `BaseException`, que Logging deberá saber
  serializar) sin necesitar lógica de despacho por tipo.
- Esta decisión es vinculante para el diseño de Logging (fase futura):
  su `on_runtime_event` debe ser, en la práctica, total (no debe existir
  una entrada de `RuntimeEventKind` para la cual pueda lanzar).
