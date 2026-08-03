# Arquitectura vigente

Este documento describe únicamente la arquitectura que existe hoy en el
repositorio. No describe fases futuras del roadmap; esas se documentan en
`PROJECT_CONTEXT.md` (estado), `docs/VISION.md` (visión de producto) y
los ADR (decisiones).

## Estado: Services (infraestructura)

Fase completada: **Foundation** (PR-001), **Runtime** (PR-002),
**Configuration** (PR-003), **Logging** (PR-004), **Services —
infraestructura** (PR-005).
Fase siguiente: **Providers** (PR-006).

## Estructura del repositorio

```
src/velora/
    __init__.py           # Metadata pública del paquete (__version__)
    cli.py                 # Entrypoint de consola `velora` (composition root)
    py.typed               # Marcador PEP 561: el paquete está tipado
    configuration/
        __init__.py         # Superficie pública de velora.configuration
        _environment.py       # Environment
        _errors.py              # Jerarquía VeloraConfigurationError
        _log_level.py             # LogLevel (propio de Configuration, ADR-0006)
        _parsing.py                # parse_enum — punto único de parseo tipado
        _settings.py                 # VeloraSettings
        _sources.py                   # ConfigSource, EnvironmentSource (único lugar con os.environ)
    logging/
        __init__.py         # Superficie pública de velora.logging
        _level.py             # LogLevel (propio de Logging, ADR-0006)
        _settings.py            # LoggingSettings
        _formatting.py            # format_event — total sobre RuntimeEventKind
        _listener.py                # RuntimeEventLogger (implementa RuntimeEventListener)
    services/
        __init__.py         # Superficie pública de velora.services
        _clock.py             # Clock, SystemClock (propios, ADR-0007)
        _id_generator.py        # IdGenerator, UUIDIdGenerator (propios, ADR-0007)
    runtime/
        __init__.py         # Superficie pública de velora.runtime
        _clock.py             # Clock, SystemClock (propios de Runtime, ADR-0007)
        _context.py            # RuntimeContext
        _errors.py               # Jerarquía VeloraRuntimeError
        _events.py                 # RuntimeEvent, RuntimeEventKind, RuntimeEventListener
        _id_generator.py             # IdGenerator, UUIDIdGenerator (propios de Runtime, ADR-0007)
        _lifecycle.py                   # Protocolo LifecycleComponent
        _runtime.py                       # Clase Runtime
        _state.py                          # RuntimeState
tests/
    test_package_metadata.py
    test_cli.py
    test_configuration_*.py       # 8 archivos
    test_logging_*.py             # 5 archivos
    test_runtime_*.py             # 8 archivos
    test_services_*.py            # 2 archivos
    test_no_direct_environ_access.py     # invariante ejecutable
docs/
    architecture.md               # Este documento
    VISION.md                       # Visión de producto (incorporada en PR-005)
    adr/                              # Registro de decisiones arquitectónicas
PROJECT_CONTEXT.md                  # Estado actual del proyecto
```

## Componentes existentes

### `velora` (paquete raíz)

Expone `__version__`, resuelto vía `importlib.metadata`.

### `velora.configuration`

Único punto de entrada de configuración tipada: `load_settings`,
`VeloraSettings` (`environment`, `log_level`), `Environment`, `LogLevel`
(propio — ADR-0006), `ConfigSource`/`EnvironmentSource` (único lugar con
`os.environ`, verificado por test), `VeloraConfigurationError` y su
jerarquía. No importa `velora.runtime`, `velora.logging` ni
`velora.services`.

### `velora.logging`

Backend real de logging de eventos del Runtime: `configure_logging`,
`RuntimeEventLogger` (implementa `RuntimeEventListener`
estructuralmente, usa `logging.Logger` construido directamente — no
`getLogger` — para no tocar el registro global), `LoggingSettings`,
`LogLevel` (propio — ADR-0006). Importa `velora.runtime` (para
`RuntimeEvent`/`RuntimeEventKind`). No importa `velora.configuration`.

### `velora.services`

Services de infraestructura (ADR-0008 distingue esta categoría de los
Services de capacidad, que todavía no existen):

- **`Clock`** / **`SystemClock`** — abstracción de "la hora actual".
- **`IdGenerator`** / **`UUIDIdGenerator`** — abstracción de "generar un
  identificador único".

Ninguno de los dos implementa `LifecycleComponent`: no tienen ningún
recurso que abrir o cerrar (ver ADR-0007). No importan
`velora.runtime`, `velora.configuration` ni `velora.logging` — son hoja
del grafo de dependencias, y satisfacen estructuralmente (PEP 544) los
protocolos homónimos que `velora.runtime` define por su cuenta.

### `velora.runtime`

El núcleo estable del sistema. Superficie pública:

- **`Runtime`** — bootstrap, lifecycle, apagado ordenado. Instancia de un
  solo uso. Ver ADR-0003. Desde PR-005, acepta `clock: Clock | None` e
  `id_generator: IdGenerator | None` inyectables; si no se dan, usa
  internamente `SystemClock()`/`UUIDIdGenerator()` — la única excepción
  documentada a "las dependencias se inyectan, nunca se crean dentro de
  las clases", justificada porque ambos defaults son deterministas, sin
  estado, y su comportamiento por defecto es literalmente "usar el mundo
  real" (ADR-0007).
- **`RuntimeState`**, **`RuntimeContext`**.
- **`Clock`** / **`SystemClock`**, **`IdGenerator`** / **`UUIDIdGenerator`**
  — protocolos e implementaciones **propios** de Runtime, no importados
  de `velora.services` (Runtime no puede depender de Services — Services
  está por encima en la capa). `velora.services.SystemClock` los
  satisface estructuralmente sin ningún import cruzado.
- **`LifecycleComponent`** — el único contrato por el que el Runtime
  conoce a un componente. Ni `Configuration`, ni `Logging`, ni los
  Services de infraestructura actuales lo implementan.
- **`RuntimeEvent`** / **`RuntimeEventKind`** / **`RuntimeEventListener`**
  — ver ADR-0004.
- **`VeloraRuntimeError`** y su jerarquía.

El Runtime no importa ni conoce Configuration, Logging, Services,
Providers, Engines, Workflows ni Extensions — solo sus propios
protocolos (`LifecycleComponent`, `RuntimeEventListener`, `Clock`,
`IdGenerator`).

### `velora.cli`

Composition root (ADR-0005, ADR-0006, ADR-0007):

1. Resuelve `VeloraSettings`. Si falla, reporta a `stderr` y sale con 1.
2. Traduce `settings.log_level` a `LoggingLogLevel` y configura
   `RuntimeEventLogger`.
3. Construye `Runtime` con el logger como listener y con
   `velora.services.SystemClock()`/`UUIDIdGenerator()` inyectados
   explícitamente en lugar de los defaults internos de `Runtime` —
   haciendo real, no solo teórica, la sustitución estructural.
4. Ejecuta el Runtime como context manager, reportando `runtime_id` y
   `environment`. Un fallo se reporta a `stderr` con código 1, además de
   lo que `RuntimeEventLogger` ya haya registrado.

## Dependencias entre componentes

```
velora.cli  →  velora.runtime
velora.cli  →  velora.configuration
velora.cli  →  velora.logging  →  velora.runtime
velora.cli  →  velora.services
```

`velora.services` no importa `velora.runtime`, `velora.configuration` ni
`velora.logging` — sus tipos satisfacen los protocolos de `velora.runtime`
únicamente por estructura (ADR-0007). `velora.configuration` y
`velora.logging` no se importan entre sí (ADR-0006). Ningún subpaquete
importa `velora.cli`. No hay dependencias externas de terceros.

## Lo que no existe todavía

Providers, Engines, Workflows, Extensions. Tampoco existen Services de
capacidad (`NarrationService`, `ImageService`, etc.) — dependen de que
exista al menos un Provider real (ADR-0008). Cualquier mención a esas
capas en otros documentos es planificación, no arquitectura vigente.
Este documento se actualizará en cada PR que introduzca una capa nueva.
