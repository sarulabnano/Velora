# ADR-0006: `LogLevel` existe por duplicado en Configuration y Logging, sin import cruzado

## Status

Accepted

## Context

`VeloraSettings` (Configuration) necesita resolver, con el mismo
mecanismo tipado que usa para todo lo demás, qué nivel de log configuró
el usuario (`VELORA_LOG_LEVEL`). `RuntimeEventLogger` (Logging) necesita
un nivel de log para configurar su backend (`logging.Logger`,
stdlib). Ambos representan, conceptualmente, "el mismo" valor.

La tentación obvia es definir un único tipo `LogLevel` en un lugar y que
el otro lo importe. Pero el grafo de dependencias de `architecture.md`
original §4 es direccional:

```
Configuration → Logging → Runtime
```

("→" = "depende de", "cada capa depende de la de abajo"). Esto permite a
Configuration depender de Logging, pero **prohíbe la dirección
contraria**: Logging nunca puede depender de Configuration — sería una
dependencia hacia arriba, la que el sistema de capas existe precisamente
para prohibir. Y ADR-0001 ya cerró la otra dirección explícitamente:
Configuration nunca importa Logging, en ningún punto de su código, para
evitar el riesgo de dependencia circular con el reporte de errores.

Con ambas direcciones cerradas, un tipo compartido `LogLevel` no tiene
dónde vivir sin violar una de las dos reglas — salvo moviéndolo a
`velora.runtime`, lo cual contaminaría el Core con un concepto que no le
pertenece ("Runtime no conoce... logging concreto").

## Decision

`LogLevel` se define dos veces, de forma independiente:

- `velora.configuration.LogLevel` — un valor de configuración como
  cualquier otro, resuelto por `parse_enum` igual que `Environment`.
- `velora.logging.LogLevel` — el nivel que el backend de logging
  entiende, con un método `to_stdlib_level()` que lo traduce a las
  constantes de `logging` (stdlib).

Ninguno de los dos módulos importa al otro. El composition root
(`velora.cli.main`) es el único lugar que conoce ambos tipos y traduce
entre ellos, por nombre de miembro (`LoggingLogLevel[level.name]`) — una
función de una línea, `_translate_log_level`, vinculada de forma
explícita a esta ADR en su docstring.

Se consideró la alternativa de tener un único `LogLevel` en un módulo
neutral nuevo (p. ej. `velora._shared` o similar) que ambos importaran.
Se descartó: introduce un módulo cuya única razón de existir es romper
un problema de capas, sin corresponder a ninguna capa real del
`architecture.md` original, y establece un precedente peligroso ("cuando
dos capas necesiten compartir un tipo, créese un módulo compartido") que
erosionaría la disciplina de capas exactamente donde más importa
protegerla.

## Consequences

- Duplicación real, pero mínima y deliberada: dos enums de cinco
  miembros cada uno, casi idénticos en nombre. El costo de mantenerlos
  sincronizados es bajo (cualquier cambio se detecta de inmediato: un
  nombre de miembro no reconocido en `_translate_log_level` lanza
  `KeyError` en tiempo de ejecución, cubierto por los tests del CLI).
- `velora.configuration` y `velora.logging` permanecen completamente
  independientes y testeables en aislamiento — ninguno de los dos
  importa al otro, confirmado por sus respectivas suites de tests, que
  no referencian el paquete opuesto en ningún punto.
- Cualquier settings futura que necesite compartir un concepto entre dos
  capas no adyacentes-por-import debe resolver la tensión de la misma
  manera: tipos independientes por capa, traducción explícita en el
  composition root — no un módulo compartido nuevo, salvo que
  corresponda a una capa real del roadmap.
