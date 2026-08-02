# ADR-0001: Configuration no depende de Logging en tiempo de import

## Status

Accepted

## Context

El roadmap congelado del proyecto establece el siguiente orden de
construcción:

```
Foundation → Runtime → Configuration → Logging → Services → ...
```

Sin embargo, el diagrama de capas de `architecture.md` establece la
siguiente cadena de dependencia:

```
... → Providers → Services → Configuration → Logging → Runtime
```

En ese diagrama, `Configuration` aparece por encima de `Logging`, lo cual
se puede leer como "Configuration depende de Logging". Si esa lectura
fuera literal, construir en el orden del roadmap (Configuration antes que
Logging) sería imposible sin una dependencia hacia adelante no resuelta.

Además, existe un riesgo de acoplamiento circular: `Logging` típicamente
necesita `Configuration` para saber cómo configurarse (nivel de log,
formato, destino), y si `Configuration` a su vez dependiera de `Logging`
para reportar sus propios errores, se formaría un ciclo de dependencia
entre dos módulos del Core.

## Decision

El diagrama de capas describe el **grafo de dependencias en tiempo de
composición** (cómo el Runtime conecta los componentes al arrancar), no el
**orden de construcción del código**. Son dos cosas distintas y no tienen
por qué coincidir.

Se establece lo siguiente como regla de diseño vinculante:

1. `Configuration` no importa `Logging` en ningún punto de su código.
2. Cuando `Configuration` encuentra un error (valor inválido, variable
   faltante, tipo incorrecto), lo representa como una excepción tipada
   propia del módulo `Configuration` (o un tipo `Result` explícito, a
   decidir en el PR de Configuration). `Configuration` nunca escribe logs
   directamente.
3. `Runtime` es el único componente que conoce tanto a `Configuration`
   como a `Logging`. Durante el bootstrap, `Runtime` intenta cargar la
   configuración; si falla, captura el error tipado y se lo entrega a
   `Logging` (o, si `Logging` todavía no está inicializado, lo escribe a
   `stderr` como último recurso) para que decida cómo registrarlo.
4. `Logging`, de forma simétrica, no importa `Configuration`. Recibe su
   propia configuración ya resuelta (un objeto tipado) como parámetro de
   inicialización inyectado por `Runtime`, no accediendo a `Configuration`
   por su cuenta.

Con esta regla, el orden de construcción del roadmap
(`Configuration` antes que `Logging`) es válido: `Configuration` se puede
construir y probar de forma completamente aislada, sin ninguna
dependencia de `Logging`.

## Consequences

- `Configuration` queda testeable de forma aislada, sin necesidad de un
  backend de logging real ni de mocks para logging.
- Se elimina cualquier posibilidad de dependencia circular entre
  `Configuration` y `Logging`.
- `Runtime` gana una responsabilidad explícita: es el punto de conexión
  entre errores de configuración y su registro. Esto refuerza (no
  contradice) su rol como orquestador central definido en
  `architecture.md` §5.
- El diagrama de capas de `architecture.md` debe leerse en adelante como
  "grafo de dependencias en tiempo de composición", no como "orden de
  construcción". Este ADR es la referencia normativa para esa lectura.
- Esta decisión es vinculante para el diseño de `Configuration` (fase
  futura) y de `Logging` (fase futura); ambos PRs deberán implementarla
  explícitamente y podrán citar este ADR en su propia documentación.
