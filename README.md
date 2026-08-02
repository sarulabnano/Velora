# Velora

Velora es una plataforma pensada para evolucionar durante al menos diez
años sin que su Runtime necesite reescribirse. Prioriza estabilidad,
mantenibilidad y extensibilidad por encima de velocidad de desarrollo
inicial.

## Estado actual

**Fase: Foundation** (PR-001). El Runtime todavía no existe; ver
[`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) para el estado detallado y
[`docs/architecture.md`](docs/architecture.md) para la arquitectura
vigente.

## Requisitos

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) como gestor de dependencias

## Uso

```bash
git clone <repo>
cd velora
uv sync
uv run velora
```

```bash
uv run velora --version
uv run velora --help
```

## Desarrollo

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

`uv run` garantiza que el comando se ejecuta con el intérprete y las
dependencias de `.venv/` del proyecto, sin importar si el entorno virtual
está activado en la shell actual. Si prefieres no escribir `uv run` cada
vez, activa el entorno explícitamente (`source .venv/bin/activate` en
Linux/macOS) y a partir de ahí `pytest`, `ruff` y `mypy` sueltos también
funcionarán.

## Filosofía

- Runtime First
- Stable Core
- Dependency Injection
- Composition over Inheritance
- Configuration over Code
- Typed Everything
- Explicit APIs
- Small Public Surface
- Fail Fast
- No Hidden Magic

Ver [`docs/architecture.md`](docs/architecture.md) para el detalle y
[`docs/adr/`](docs/adr/) para el historial de decisiones.

## Roadmap

```
Foundation → Runtime → Configuration → Logging → Services →
Providers → Engines → Workflows → Extensions
```

Este orden está congelado: cada fase solo depende de las anteriores.

## Licencia

MIT — ver [`LICENSE`](LICENSE).
