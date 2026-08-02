# ADR-0005: Configuration se carga en el composition root, no dentro de la clase Runtime

## Status

Accepted — refina ADR-0001, no la contradice ni la reemplaza.

## Context

ADR-0001 estableció que `Configuration` no depende de `Logging` en
tiempo de import, y que **"Runtime es el único componente que conoce
tanto a Configuration como a Logging"**, siendo quien conecta los
errores de `Configuration` con `Logging` durante el bootstrap. Esa ADR
se escribió antes de que existiera la clase `Runtime` (PR-002) y antes
de decidir su forma final.

Con `Runtime` ya implementado (ADR-0003), su contrato de composición es
deliberadamente estrecho: solo conoce `LifecycleComponent` y
`RuntimeEventListener`. Modelar `Configuration` como un
`LifecycleComponent` para que `Runtime` la "conociera" directamente
tiene un problema semántico: `Configuration` no es un recurso con
arranque/parada — no abre conexiones, no tiene hilos, no tiene nada que
cerrar. Forzarla a implementar `start()`/`stop()` sería una interfaz sin
contenido real, exactamente el tipo de "magia" superficial que el
manifiesto de ingeniería prohíbe.

Hace falta precisar qué significa, en código, que "Runtime conecte los
errores de Configuration con Logging".

## Decision

La palabra "Runtime" en ADR-0001 se interpreta como **la capa Runtime**
(architecture.md, la capa base del diagrama), no literalmente la clase
`velora.runtime.Runtime`. Su encarnación concreta hoy es el composition
root: `velora.cli.main`, el único lugar del repositorio donde se
construyen y conectan las piezas del sistema.

En consecuencia:

1. `velora.configuration` no importa `velora.runtime` en ningún punto.
   Es una hoja del grafo de dependencias, tan aislada como sea posible.
2. `velora.configuration` no implementa `LifecycleComponent`. Se resuelve
   una sola vez, antes de construir el `Runtime`, mediante
   `load_settings()` (o `VeloraSettings.from_source(...)` con una fuente
   inyectada).
3. El composition root (`velora.cli.main`) resuelve `Configuration`
   primero. Si falla, reporta el error tipado exactamente como reporta
   hoy un `VeloraRuntimeError` — sin haber construido ni arrancado ningún
   `Runtime`, porque no hay nada que apagar de forma ordenada todavía.
4. Cuando `Logging` exista (PR-004), el composition root la conectará de
   la misma manera: construida a partir de valores ya resueltos de
   `Configuration`, e inyectada al `Runtime` como
   `RuntimeEventListener`. Ni `Configuration` ni `Runtime` importarán
   `Logging` directamente en ningún momento.

## Consequences

- `velora.configuration` es trivialmente testeable en aislamiento total
  (confirmado: cero imports de `velora.runtime` en sus tests).
- El composition root acumula la responsabilidad explícita de "cablear"
  el sistema. Esto es intencional y coherente con Dependency Injection:
  el cableado vive en un solo lugar conocido, no disperso.
- Esta decisión es vinculante para PR-004 (Logging): su construcción a
  partir de `Configuration` y su inyección en `Runtime` como listener
  ocurren en `velora.cli.main`, no dentro de `Runtime` ni dentro de
  `Configuration`.
- ADR-0001 permanece vigente en su decisión central (Configuration nunca
  importa Logging, produce errores tipados); esta ADR únicamente aclara
  qué módulo concreto realiza la conexión.
