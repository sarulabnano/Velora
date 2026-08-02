# ADR-0003: Máquina de estados del Runtime, instancia de un solo uso, y semántica de fallo

## Status

Accepted

## Context

`architecture.md` §5 asigna al Runtime: bootstrap, lifecycle, contexto de
ejecución, apagado ordenado y manejo de errores fatales. Ninguno de esos
términos está definido operacionalmente todavía. Antes de escribir
`Runtime`, hacía falta fijar: qué estados existen, si una instancia puede
reiniciarse, y qué ocurre exactamente cuando un componente falla al
arrancar o al detenerse — porque estas decisiones determinan la forma de
la API pública y son extremadamente costosas de cambiar después (el
Runtime es la capa que "permanece prácticamente inmutable con el paso de
los años").

## Decision

### Máquina de estados

```
NOT_STARTED -> STARTING -> RUNNING -> STOPPING -> STOPPED
STARTING    -> FAILED   (un componente falló al iniciar)
STOPPING    -> FAILED   (uno o más componentes fallaron al detenerse)
```

### Instancia de un solo uso

Un `Runtime` no vuelve a `NOT_STARTED` desde ningún otro estado. Para
volver a ejecutar, se construye una instancia nueva. Un `Runtime`
reiniciable es un caso de uso legítimo pero añade una dimensión de
complejidad (¿se reconstruye el contexto? ¿se reinyectan los mismos
componentes o unos nuevos? ¿qué pasa si un componente no es
reutilizable?) que el Core no necesita resolver todavía. Si aparece la
necesidad, se añade como una capacidad nueva sin romper la API existente
(Open/Closed).

### Fallo durante `start()`

Los componentes se inician en el orden dado al constructor. Si uno falla:

1. El Runtime pasa a `FAILED`.
2. Se emite un evento `FATAL_ERROR`.
3. Los componentes ya iniciados se detienen, en orden inverso,
   *best-effort* (un fallo durante este unwind no aborta el unwind de
   los demás; se emite como evento pero no se propaga — ver
   `_unwind_after_bootstrap_failure`).
4. Se lanza `RuntimeBootstrapError`, encadenada (`__cause__`) a la
   excepción original del componente. El fallo del unwind, si lo hay,
   nunca reemplaza ni oculta la causa original.

### Fallo durante `stop()`

A diferencia del arranque, la parada es **exhaustiva**: si un componente
falla al detenerse, los demás igual se intentan detener, en orden
inverso completo. Al final, si hubo fallos, se lanza
`RuntimeShutdownError` encadenada a la primera excepción. Esto es
deliberadamente distinto del comportamiento de arranque: parar es una
operación de limpieza de recursos (conexiones, archivos, hilos); dejar de
intentar detener el resto de componentes porque uno falló dejaría
recursos huérfanos, que es peor que reportar un fallo agregado.

### No hay reentrada / no hay concurrencia

Esta implementación no es thread-safe. Llamadas concurrentes a
`start()`/`stop()` desde múltiples hilos sobre la misma instancia no
están soportadas; el resultado es indefinido. Se documenta explícitamente
en el docstring de `Runtime` en vez de fingir una garantía que el código
no cumple.

## Consequences

- La API pública de `Runtime` es pequeña: `start()`, `stop()`, `state`,
  `context`, y soporte de context manager (`__enter__`/`__exit__`) como
  azúcar sintáctica sobre lo mismo.
- Cualquier componente futuro (Configuration, Logging, Services...) que
  implemente `LifecycleComponent` hereda automáticamente esta semántica
  de arranque *fail-fast-con-unwind* y parada *exhaustiva*, sin tener que
  reimplementarla.
- Un `Runtime` fallido (`FAILED`) es terminal: no intenta auto-recuperarse
  ni permite reintentar `start()`. La recuperación es responsabilidad de
  quien orquesta el proceso (por ejemplo, la capa de aplicación que
  invoque a `Runtime`, no el propio Runtime).
- Esta decisión es vinculante para todo componente que implemente
  `LifecycleComponent` en fases futuras: debe asumir que su `stop()`
  puede ser invocado incluso si `start()` de otro componente falló
  después del suyo (unwind), y que su propio `stop()` fallido no impedirá
  que otros componentes también sean detenidos.
