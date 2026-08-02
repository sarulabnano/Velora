# Arquitectura vigente

Este documento describe únicamente la arquitectura que existe hoy en el
repositorio. No describe fases futuras del roadmap; esas se documentan en
`PROJECT_CONTEXT.md` (estado) y en los ADR (decisiones).

## Estado: Logging

Fase completada: **Foundation** (PR-001), **Runtime** (PR-002),
**Configuration** (PR-003), **Logging** (PR-004).
Fase siguiente: **Services** (PR-005).

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
        _log_level.py             # LogLevel (propio de Configuration, ver ADR-0006)
        _parsing.py                # parse_enum — punto único de parseo tipado
        _settings.py                 # VeloraSettings
        _sources.py                   # ConfigSource, EnvironmentSource (único lugar con os.environ)
    logging/
        __init__.py         # Superficie pública de velora.logging
        _level.py             # LogLevel (propio de Logging, ver ADR-0006)
        _settings.py            # LoggingSettings
        _formatting.py            # format_event — total sobre RuntimeEventKind
        _listener.py                # RuntimeEventLogger (implementa RuntimeEventListener)
    runtime/
        __init__.py         # Superficie pública de velora.runtime
        _context.py          # RuntimeContext
        _errors.py             # Jerarquía VeloraRuntimeError
        _events.py               # RuntimeEvent, RuntimeEventKind, RuntimeEventListener
        _lifecycle.py               # Protocolo LifecycleComponent
        _runtime.py                   # Clase Runtime
        _state.py                      # RuntimeState
tests/
    test_package_metadata.py
    test_cli.py
    test_configuration_*.py       # 7 archivos, uno por módulo de Configuration
    test_logging_*.py             # 5 archivos, uno por módulo de Logging
    test_runtime_*.py             # 6 archivos, uno por módulo de Runtime
    test_no_direct_environ_access.py     # invariante ejecutable, no solo documentada
docs/
    architecture.md               # Este documento
    adr/                            # Registro de decisiones arquitectónicas
PROJECT_CONTEXT.md                  # Estado actual del proyecto
```

## Componentes existentes

### `velora` (paquete raíz)

Expone una única variable pública: `__version__`, resuelta en tiempo de
ejecución vía `importlib.metadata` (`__all__ = ["__version__"]`).

### `velora.configuration`

El único punto de entrada por el que la configuración se transforma en
objetos tipados. Superficie pública:

- **`load_settings(source=None)`** — con `source=None` usa
  `EnvironmentSource` (variables de entorno reales).
- **`VeloraSettings`** — dataclass congelado: `environment: Environment`,
  `log_level: LogLevel`. Se construye únicamente vía
  `VeloraSettings.from_source(...)`.
- **`Environment`** — enum `DEVELOPMENT` / `STAGING` / `PRODUCTION`.
- **`LogLevel`** — enum `DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`,
  propio de Configuration. Ver ADR-0006: no es el mismo tipo que
  `velora.logging.LogLevel`, deliberadamente.
- **`ConfigSource`** / **`EnvironmentSource`** — la única implementación,
  y el único lugar de todo el código fuente donde se lee `os.environ`
  (invariante verificada por `tests/test_no_direct_environ_access.py`).
- **`VeloraConfigurationError`** y su jerarquía
  (`MissingConfigurationValueError`, `InvalidConfigurationValueError`).

`velora.configuration` no importa `velora.runtime`, `velora.logging` ni
`velora.cli`. Es una hoja del grafo de dependencias (ADR-0005, ADR-0006).

### `velora.logging`

El backend que decide cómo se registran los eventos del Runtime
(architecture.md original §7). Superficie pública:

- **`configure_logging(settings, *, stream=None, name="velora")`** —
  construye un `RuntimeEventLogger`. `stream` por defecto es
  `sys.stderr`, leído en el momento de la llamada.
- **`RuntimeEventLogger`** — implementa `RuntimeEventListener`
  *estructuralmente* (no importa `velora.runtime.RuntimeEventListener`
  para heredar de él, solo para tipar). Usa `logging.Logger(name, ...)`
  construido directamente — no `logging.getLogger(name)` — para no tocar
  el registro global de la stdlib ("No Singletons Globales"). Eventos
  `FATAL_ERROR` se registran a nivel `ERROR`; el resto, a nivel `INFO`.
  No captura excepciones de la llamada a `logging` subyacente (ADR-0004:
  un fallo ahí no es "operación normal").
- **`LoggingSettings`** — dataclass congelado: `level: LogLevel`.
- **`LogLevel`** — propio de Logging, con `to_stdlib_level() -> int`. No
  es el mismo tipo que `velora.configuration.LogLevel` (ADR-0006).

`velora.logging` importa `velora.runtime` (para los tipos `RuntimeEvent`,
`RuntimeEventKind` que consume) — dependencia hacia abajo, permitida por
el diagrama de capas. No importa `velora.configuration` (ADR-0006) ni
`velora.cli`. `velora.runtime` nunca importa `velora.logging`.

**Nota:** `import logging` dentro de los módulos de este paquete resuelve
al módulo estándar de Python, no a sí mismo — Python 3 usa imports
absolutos por defecto y este paquete nunca es una entrada de nivel
superior en `sys.path`. Verificado empíricamente antes de asumirlo.

### `velora.runtime`

El núcleo estable del sistema (architecture.md original §5). Superficie
pública, deliberadamente pequeña:

- **`Runtime`** — bootstrap, lifecycle, apagado ordenado. Instancia de un
  solo uso: `NOT_STARTED → STARTING → RUNNING → STOPPING → STOPPED`, con
  transición a `FAILED` si un componente falla al iniciar o detenerse.
  Ver ADR-0003.
- **`RuntimeState`**, **`RuntimeContext`**.
- **`LifecycleComponent`** — el único contrato por el que el Runtime
  conoce a un componente. Ni `Configuration` ni `Logging` lo implementan
  (ver ADR-0005): ninguno de los dos es un recurso con arranque/parada.
- **`RuntimeEvent`** / **`RuntimeEventKind`** / **`RuntimeEventListener`**
  — ver ADR-0004. `RuntimeEventLogger` (Logging) es hoy el único
  listener real.
- **`VeloraRuntimeError`** y su jerarquía.

El Runtime no importa ni conoce Configuration, Logging, Providers,
Engines, Workflows ni Extensions — solo los protocolos
`LifecycleComponent` y `RuntimeEventListener`.

### `velora.cli`

Entrypoint de consola registrado como `velora`
(`[project.scripts]`). Soporta `--version` y `--help` (sin cambios desde
Foundation, ADR-0002). Es el **composition root** (ADR-0005, ADR-0006):

1. Resuelve `VeloraSettings` (vía `settings_loader` inyectable). Si
   falla, imprime a `stderr` y sale con código 1 — nada más se construye.
2. Traduce `settings.log_level` (Configuration) a `LoggingLogLevel`
   (Logging) por nombre (`_translate_log_level`), y configura
   `RuntimeEventLogger` (vía `logging_factory` inyectable).
3. Construye `Runtime` con el logger como único listener (vía
   `runtime_factory` inyectable) y lo ejecuta como context manager,
   reportando `runtime_id` y `environment` a `stdout`.
4. Si el Runtime falla, imprime a `stderr` y sale con código 1 — además
   de lo que `RuntimeEventLogger` ya haya registrado de forma
   independiente (el mensaje de `stderr` es la garantía visible siempre,
   sin importar el nivel de log configurado; el registro estructurado es
   el detalle, sujeto a `VELORA_LOG_LEVEL`).

## Dependencias entre componentes

```
velora.cli  →  velora.runtime
velora.cli  →  velora.configuration
velora.cli  →  velora.logging  →  velora.runtime
```

`velora.configuration` y `velora.logging` no se importan entre sí
(ADR-0006). Ninguno de los tres subpaquetes importa `velora.cli`. No hay
dependencias externas de terceros en `dependencies` de `pyproject.toml`.

## Lo que no existe todavía

Services, Providers, Engines, Workflows y Extensions no existen en el
repositorio. Cualquier mención a esas capas en otros documentos
(`PROJECT_CONTEXT.md`, ADR) es planificación, no arquitectura vigente.
Este documento se actualizará en cada PR que introduzca una capa nueva.
