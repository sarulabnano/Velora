# Arquitectura vigente

Este documento describe únicamente la arquitectura que existe hoy en el
repositorio. No describe fases futuras del roadmap; esas se documentan en
`PROJECT_CONTEXT.md` (estado) y en los ADR (decisiones).

## Estado: Runtime

Fase completada: **Foundation** (PR-001), **Runtime** (PR-002).
Fase siguiente: **Configuration** (PR-003).

## Estructura del repositorio

```
src/velora/
    __init__.py           # Metadata pública del paquete (__version__)
    cli.py                 # Entrypoint de consola `velora`
    py.typed               # Marcador PEP 561: el paquete está tipado
    runtime/
        __init__.py         # Superficie pública de velora.runtime
        _context.py          # RuntimeContext
        _errors.py            # Jerarquía VeloraRuntimeError
        _events.py             # RuntimeEvent, RuntimeEventKind, RuntimeEventListener
        _lifecycle.py           # Protocolo LifecycleComponent
        _runtime.py              # Clase Runtime
        _state.py                 # RuntimeState
tests/
    test_package_metadata.py
    test_cli.py
    test_runtime.py               # Ciclo de vida de Runtime (bulk de tests)
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
  `stop()`. Configuration, Logging y cualquier fase futura deben
  implementarlo para participar en el ciclo de vida; el Runtime nunca
  importa esas fases directamente.
- **`RuntimeEvent`** / **`RuntimeEventKind`** / **`RuntimeEventListener`**
  — el Runtime nunca escribe logs; emite `RuntimeEvent` a los listeners
  inyectados. Ver ADR-0004 para por qué es un dataclass plano con un
  enum de tipo, en vez de una jerarquía de clases, y por qué una
  excepción de un listener interrumpe el Runtime en vez de aislarse.
- **`VeloraRuntimeError`** y su jerarquía
  (`RuntimeAlreadyStartedError`, `RuntimeNotRunningError`,
  `RuntimeBootstrapError`, `RuntimeShutdownError`) — nombrada así, y no
  `RuntimeError`, para no colisionar por nombre con la excepción builtin
  de Python dentro de un módulo llamado `runtime`.

El Runtime no importa ni conoce Configuration, Logging, Providers,
Engines, Workflows ni Extensions — solo los protocolos
`LifecycleComponent` y `RuntimeEventListener`.

### `velora.cli`

Entrypoint de consola registrado como `velora` en `pyproject.toml`
(`[project.scripts]`). Soporta `--version` y `--help` (sin cambios desde
Foundation, ADR-0002). Por defecto, construye un `Runtime` (vía un
`runtime_factory` inyectable, sin componentes ni listeners todavía —
Configuration y Logging aún no existen), lo ejecuta como context manager,
y reporta su `runtime_id`. Si el Runtime falla, el CLI captura
`VeloraRuntimeError`, imprime el error a `stderr` y sale con código 1.

## Dependencias entre componentes

```
velora.cli  →  velora.runtime  →  velora
```

`velora.runtime` no depende de `velora.cli` ni de `velora` más allá de
que ambos son parte de la misma distribución instalada. No hay
dependencias externas de terceros en `dependencies` de `pyproject.toml`.

## Lo que no existe todavía

Configuration, Logging, Services, Providers, Engines, Workflows y
Extensions no existen en el repositorio. Cualquier mención a esas capas
en otros documentos (`PROJECT_CONTEXT.md`, ADR) es planificación, no
arquitectura vigente. Este documento se actualizará en cada PR que
introduzca una capa nueva.
