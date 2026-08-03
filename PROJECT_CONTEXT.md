# PROJECT_CONTEXT

Este documento resume el estado actual de Velora. No duplica los ADR ni
`docs/VISION.md`; los referencia.

## Último PR

**PR-005 — Services (infraestructura).**

## Milestone activa

**Services** (completada — solo Services de infraestructura; los
Services de capacidad esperan a Providers, ver ADR-0008). Próxima:
**Providers** (PR-006).

## Roadmap (congelado, no modificable)

```
Foundation → Runtime → Configuration → Logging → Services →
Providers → Engines → Workflows → Extensions
```

## Documento de visión

`docs/VISION.md` — visión de producto: Velora como plataforma de
automatización de producción audiovisual con IA. Incorporado en PR-005.
Es la fuente de verdad del dominio; no es vinculante arquitectónicamente
por sí solo — las discrepancias con lo construido se resuelven vía ADR
(ver ADR-0008, la primera).

## Componentes que existen hoy

- `velora` — paquete raíz, expone `__version__`.
- `velora.cli` — entrypoint de consola `velora`, composition root; por
  defecto resuelve `Configuration`, configura `Logging`, construye
  `Runtime` inyectando `SystemClock`/`UUIDIdGenerator` de
  `velora.services`, y reporta `runtime_id` y `environment`.
- `velora.runtime` — núcleo estable: `Runtime`, `RuntimeState`,
  `RuntimeContext`, `LifecycleComponent`, `RuntimeEvent`,
  `RuntimeEventKind`, `RuntimeEventListener`, `Clock`, `SystemClock`,
  `IdGenerator`, `UUIDIdGenerator` (estos dos últimos con default interno
  si no se inyectan — la única excepción documentada a "nunca se crean
  dentro de las clases", ver ADR-0007), `VeloraRuntimeError` y su
  jerarquía.
- `velora.configuration` — único punto de entrada de configuración
  tipada: `load_settings`, `VeloraSettings`, `Environment`, `LogLevel`,
  `ConfigSource`, `EnvironmentSource`, `VeloraConfigurationError` y su
  jerarquía.
- `velora.logging` — backend de logging real: `configure_logging`,
  `RuntimeEventLogger`, `LoggingSettings`, `LogLevel` (propio).
- `velora.services` — Services de infraestructura: `Clock`/`SystemClock`,
  `IdGenerator`/`UUIDIdGenerator`. Satisfacen estructuralmente los
  protocolos homónimos de `velora.runtime` sin ningún import cruzado
  (ADR-0007). No dependen de `velora.configuration`, `velora.logging` ni
  `velora.runtime`.

Ver `docs/architecture.md` para el detalle de cada símbolo.

## Componentes que NO existen todavía

Providers, Engines, Workflows, Extensions. Tampoco existen Services de
capacidad (`NarrationService`, `ImageService`, etc. — ver ADR-0008):
esperan a que exista al menos un Provider real que los respalde.

## Decisiones vigentes (ADR)

- **ADR-0001** — `Configuration` no depende de `Logging` en tiempo de
  import. Refinada por ADR-0005.
- **ADR-0002** — El entrypoint CLI es funcionalidad real y permanente,
  extendido en cada fase, nunca reemplazado.
- **ADR-0003** — Máquina de estados del Runtime, instancia de un solo
  uso, arranque fail-fast-con-unwind, parada exhaustiva.
- **ADR-0004** — `RuntimeEvent` como dataclass plano + enum. Excepciones
  de listeners no se capturan.
- **ADR-0005** — La "Runtime" que conecta Configuration y Logging es el
  composition root (`velora.cli.main`), no la clase `Runtime`.
  `Configuration` no implementa `LifecycleComponent`.
- **ADR-0006** — `LogLevel` existe por duplicado, independiente, en
  `velora.configuration` y `velora.logging` — ninguno importa al otro.
- **ADR-0007** — `Runtime` gana `clock`/`id_generator` inyectables
  (protocolos propios, `SystemClock`/`UUIDIdGenerator` como default
  interno — única excepción documentada a "nunca crear dependencias
  dentro de la clase", justificada por ser deterministas/sin estado).
  `velora.services` provee implementaciones que los satisfacen
  estructuralmente sin importar `velora.runtime`. El composition root
  inyecta explícitamente las de Services, demostrando la sustitución
  real, no solo teórica.
- **ADR-0008** — Resuelve la contradicción entre AGENT.md original
  (`Providers → Services`) y `docs/VISION.md` (`Services → Providers`):
  se adopta la dirección de VISION.md. Establece dos categorías de
  Service (infraestructura vs. capacidad) y el diagrama de capas
  canónico vigente, que integra ambos documentos. Vinculante para
  PR-006 (Providers) y para cualquier Service de capacidad futuro.

## Criterios de aceptación vigentes

Desde un repositorio limpio:

```
git clone <repo>
uv sync
uv run velora
uv run pytest
```

Todo debe ejecutarse sin errores. `pytest` debe invocarse a través del
entorno gestionado por `uv` (`uv run pytest`, o con `.venv` activado).
El Core (`velora`, `velora.cli`, `velora.runtime`, `velora.configuration`,
`velora.logging`, `velora.services`) mantiene cobertura de pruebas ≥90%
como gate de aceptación; PR-005 cierra con 100%.

`os.environ` solo puede leerse en
`src/velora/configuration/_sources.py`; verificado por
`tests/test_no_direct_environ_access.py`.

## Próximo paso

**PR-006 — Providers.** Primer PR con dependencias externas reales
(SDKs de OpenAI, Anthropic, etc. — ver `docs/VISION.md`). Debe: (a)
definir contratos tipados por dominio (texto/IA, voz, imagen, video,
música, traducción — no un `Provider` genérico único, dado que cada
dominio tiene una forma de entrada/salida distinta); (b) los Providers
"nunca contienen lógica de negocio" (VISION.md) — son adaptadores puros;
(c) evaluar si un Provider concreto necesita `LifecycleComponent` (p. ej.
un cliente HTTP con conexión persistente sí; una llamada stateless no).
Tras PR-006, el primer Service de capacidad (probablemente
`NarrationService`, ver ADR-0008) queda habilitado para un PR posterior.
