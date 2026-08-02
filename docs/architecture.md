# Arquitectura vigente

Este documento describe únicamente la arquitectura que existe hoy en el
repositorio. No describe fases futuras del roadmap; esas se documentan en
`PROJECT_CONTEXT.md` (estado) y en los ADR (decisiones).

## Estado: Configuration

Fase completada: **Foundation** (PR-001), **Runtime** (PR-002),
**Configuration** (PR-003).
Fase siguiente: **Logging** (PR-004).

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
        _parsing.py               # parse_enum — punto único de parseo tipado
        _settings.py                # VeloraSettings
        _sources.py                  # ConfigSource, EnvironmentSource (único lugar con os.environ)
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
    test_configuration_environment.py
    test_configuration_errors.py
    test_configuration_load_settings.py
    test_configuration_parsing.py
    test_configuration_settings.py
    test_configuration_sources.py
    test_no_direct_environ_access.py     # invariante ejecutable, no solo documentada
    test_runtime.py
    test_runtime_context.py
    test_runtime_errors.py
    test_runtime_events.py
    test_runtime_lifecycle.py
    test_runtime_state.py
docs/
    architecture.md               # Este documento
    adr/                            # Registro de decisiones arquitectónicas
PROJECT_CONTEXT.md                  # Estado actual del proyecto
```

## Componentes existentes

### `velora` (paquete raíz)

Expone una única variable pública: `__version__`. Su valor se resuelve en
tiempo de ejecución desde los metadatos de la distribución instalada
(`importlib.metadata`), nunca como literal duplicado. La superficie
pública se mantiene deliberadamente mínima (`__all__ = ["__version__"]`).

### `velora.configuration`

El único punto de entrada por el que la configuración se transforma en
objetos tipados (architecture.md original §6). Superficie pública:

- **`load_settings(source=None)`** — función de conveniencia; con
  `source=None` usa `EnvironmentSource` (variables de entorno reales).
- **`VeloraSettings`** — dataclass congelado con la configuración
  resuelta. Hoy: `environment: Environment`. Se construye únicamente vía
  `VeloraSettings.from_source(...)`.
- **`Environment`** — enum `DEVELOPMENT` / `STAGING` / `PRODUCTION`.
- **`ConfigSource`** — `Protocol` estructural (`get(key) -> str | None`).
  **`EnvironmentSource`** — la única implementación, y el único lugar de
  todo el código fuente donde se lee `os.environ` (invariante verificada
  por `tests/test_no_direct_environ_access.py`, no solo documentada).
- **`VeloraConfigurationError`** y su jerarquía
  (`MissingConfigurationValueError`, `InvalidConfigurationValueError`).

`velora.configuration` no importa `velora.runtime` ni `velora.cli`. Es
una hoja del grafo de dependencias (ver ADR-0005).

### `velora.runtime`

El núcleo estable del sistema (architecture.md original §5). Superficie
pública, deliberadamente pequeña:

- **`Runtime`** — bootstrap, lifecycle, apagado ordenado. Instancia de un
  solo uso: `NOT_STARTED → STARTING → RUNNING → STOPPING → STOPPED`, con
  transición a `FAILED` si un componente falla al iniciar o detenerse.
  Ver ADR-0003 para la máquina de estados y la semántica de fallo.
- **`RuntimeState`** — enum de los estados anteriores.
- **`RuntimeContext`** — metadata inmutable de una ejecución
  (`runtime_id`, `started_at`), inyectada a cada componente en `start()`
  y `stop()`.
- **`LifecycleComponent`** — el único contrato por el que el Runtime
  conoce a un componente. `Protocol` estructural con `name`, `start()`,
  `stop()`. `Configuration` no lo implementa — ver ADR-0005 para por qué.
- **`RuntimeEvent`** / **`RuntimeEventKind`** / **`RuntimeEventListener`**
  — el Runtime nunca escribe logs; emite `RuntimeEvent` a los listeners
  inyectados. Ver ADR-0004.
- **`VeloraRuntimeError`** y su jerarquía
  (`RuntimeAlreadyStartedError`, `RuntimeNotRunningError`,
  `RuntimeBootstrapError`, `RuntimeShutdownError`).

El Runtime no importa ni conoce Configuration, Logging, Providers,
Engines, Workflows ni Extensions — solo los protocolos
`LifecycleComponent` y `RuntimeEventListener`.

### `velora.cli`

Entrypoint de consola registrado como `velora` en `pyproject.toml`
(`[project.scripts]`). Soporta `--version` y `--help` (sin cambios desde
Foundation, ADR-0002). Es el **composition root** (ADR-0005): por
defecto, primero resuelve `VeloraSettings` (vía `settings_loader`
inyectable), y si eso tiene éxito, construye un `Runtime` (vía
`runtime_factory` inyectable, sin componentes ni listeners todavía —
Logging aún no existe) y lo ejecuta como context manager, reportando su
`runtime_id` y el `environment` resuelto. Un fallo de `Configuration` se
reporta sin haber construido ningún `Runtime`; un fallo de `Runtime` se
reporta tras el apagado ordenado de lo que alcanzó a iniciarse. Ambos
casos: mensaje a `stderr`, código de salida 1.

## Dependencias entre componentes

```
velora.cli  →  velora.runtime
velora.cli  →  velora.configuration
```

`velora.runtime` y `velora.configuration` no dependen entre sí ni de
`velora.cli`. No hay dependencias externas de terceros en `dependencies`
de `pyproject.toml`.

## Lo que no existe todavía

Logging, Services, Providers, Engines, Workflows y Extensions no existen
en el repositorio. Cualquier mención a esas capas en otros documentos
(`PROJECT_CONTEXT.md`, ADR) es planificación, no arquitectura vigente.
Este documento se actualizará en cada PR que introduzca una capa nueva.
