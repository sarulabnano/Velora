# Velora

Velora es una plataforma pensada para evolucionar durante al menos diez
años sin que su Runtime necesite reescribirse. Prioriza estabilidad,
mantenibilidad y extensibilidad por encima de velocidad de desarrollo
inicial.

## Estado actual

**Fase: Configuration** (PR-003). Ver
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

`uv run velora`, sin flags, resuelve la configuración, bootstrapea el
Runtime, imprime su `runtime_id` de ejecución y el entorno resuelto, y lo
detiene de forma ordenada:

```
velora 0.1.0 — runtime 97811f88-8968-4a89-a392-c8b02a856fbb running (development).
velora 0.1.0 — runtime stopped cleanly.
```

El entorno se controla con la variable `VELORA_ENVIRONMENT`
(`development` por defecto, `staging`, o `production`):

```bash
VELORA_ENVIRONMENT=production uv run velora
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
