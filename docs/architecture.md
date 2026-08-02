# Arquitectura vigente

Este documento describe únicamente la arquitectura que existe hoy en el
repositorio. No describe fases futuras del roadmap; esas se documentan en
`PROJECT_CONTEXT.md` (estado) y en los ADR (decisiones).

## Estado: Foundation

Fase completada: **Foundation** (PR-001).
Fase siguiente: **Runtime** (PR-002).

## Estructura del repositorio

```
src/velora/
    __init__.py     # Metadata pública del paquete (__version__)
    cli.py           # Entrypoint de consola `velora`
    py.typed         # Marcador PEP 561: el paquete está tipado
tests/
    test_package_metadata.py
    test_cli.py
docs/
    architecture.md  # Este documento
    adr/             # Registro de decisiones arquitectónicas
PROJECT_CONTEXT.md   # Estado actual del proyecto
```

## Componentes existentes

### `velora` (paquete raíz)

Expone una única variable pública: `__version__`. Su valor se resuelve en
tiempo de ejecución desde los metadatos de la distribución instalada
(`importlib.metadata`), nunca como literal duplicado. La superficie
pública se mantiene deliberadamente mínima (`__all__ = ["__version__"]`).

### `velora.cli`

Entrypoint de consola registrado como `velora` en `pyproject.toml`
(`[project.scripts]`). Implementado con `argparse`. Soporta `--version` y
`--help`. No depende del Runtime porque el Runtime todavía no existe; ver
ADR-0002 para la justificación de por qué esto no es un stub.

## Dependencias entre componentes

`velora.cli` depende de `velora` (para leer `__version__`). No existen
más dependencias internas en esta fase. No hay dependencias externas de
terceros en `dependencies` de `pyproject.toml`.

## Lo que no existe todavía

Runtime, Configuration, Logging, Services, Providers, Engines, Workflows
y Extensions no existen en el repositorio. Cualquier mención a esas capas
en otros documentos (`PROJECT_CONTEXT.md`, ADR) es planificación, no
arquitectura vigente. Este documento se actualizará en cada PR que
introduzca una capa nueva.
