# Arquitectura vigente

Este documento describe únicamente la arquitectura que existe hoy en el
repositorio. No describe fases futuras del roadmap; esas se documentan en
`PROJECT_CONTEXT.md` (estado), `docs/VISION.md` (visión de producto) y
los ADR (decisiones).

## Estado: Providers

Fase completada: **Foundation** (PR-001), **Runtime** (PR-002),
**Configuration** (PR-003), **Logging** (PR-004), **Services —
infraestructura** (PR-005), **Providers — text_generation** (PR-006).
Fase siguiente: **Engines** (PR-007), o un segundo dominio de Providers.

## Estructura del repositorio

```
src/velora/
    __init__.py           # Metadata pública del paquete (__version__)
    cli.py                 # Entrypoint de consola `velora` (composition root)
    py.typed               # Marcador PEP 561: el paquete está tipado
    configuration/           # Ver secciones anteriores de este documento
    logging/                 # (sin cambios en este PR)
    services/                 # Clock, IdGenerator (infraestructura, PR-005)
    runtime/                   # (sin cambios funcionales en este PR)
    providers/
        __init__.py         # Jerarquía de error compartida entre dominios
        _errors.py            # VeloraProviderError y su jerarquía
        text_generation/
            __init__.py         # Superficie pública del dominio
            _types.py             # Role, Message, TextGenerationRequest/Result
            _protocol.py            # TextGenerationProvider
            _anthropic.py             # AnthropicTextGenerationProvider (real, requiere extra)
tests/
    test_package_metadata.py
    test_cli.py
    test_configuration_*.py       # 8 archivos
    test_logging_*.py             # 5 archivos
    test_runtime_*.py             # 8 archivos
    test_services_*.py            # 2 archivos
    test_providers_*.py           # 4 archivos
    test_no_direct_environ_access.py     # invariante ejecutable
docs/
    architecture.md               # Este documento
    VISION.md                       # Visión de producto
    adr/                              # Registro de decisiones arquitectónicas
PROJECT_CONTEXT.md                  # Estado actual del proyecto
```

## Componentes existentes

### `velora`, `velora.configuration`, `velora.logging`, `velora.runtime`, `velora.services`

Sin cambios funcionales de superficie pública en este PR, salvo:
`velora.runtime` expone también `Clock`/`SystemClock`/`IdGenerator`/
`UUIDIdGenerator` (desde PR-005). Ver el ADR correspondiente de cada uno
(ADR-0001 a ADR-0007) para el detalle completo.

### `velora.providers`

Paquete raíz: solo la jerarquía de error compartida entre dominios
(ADR-0009):

- **`VeloraProviderError`** (base) → `ProviderAuthenticationError`,
  `ProviderRateLimitError`, `ProviderConnectionError`,
  `ProviderRequestError`.

No contiene lógica ni contratos de dominio — esos viven en cada
subpaquete de dominio.

### `velora.providers.text_generation`

Primer dominio de Provider (ADR-0009: dominio propio, no un `Provider`
genérico):

- **`TextGenerationProvider`** — el único contrato que el resto del
  sistema conocerá (un futuro `NarrationService`, ADR-0008, dependerá de
  esto, nunca de una clase concreta). Síncrono, sin streaming
  (deliberado — ver ADR-0009).
- **`Message`**, **`Role`** (`USER`/`ASSISTANT`), **`TextGenerationRequest`**
  (`messages`, `max_tokens`, `system`, `temperature`),
  **`TextGenerationResult`** (`text`, `stop_reason`, `input_tokens`,
  `output_tokens`) — provider-agnósticos, no mencionan a ningún vendor.
- **`AnthropicTextGenerationProvider`** — primera implementación real.
  Implementa `~velora.runtime.LifecycleComponent`: `start()` construye
  el cliente del SDK (pool de conexiones HTTP real); `stop()` lo cierra
  — el primer implementador no trivial de ese contrato en el código
  base. Traduce las excepciones propias del SDK de Anthropic
  (`AuthenticationError`, `RateLimitError`, `APIConnectionError`,
  `APIStatusError`) a la jerarquía compartida de `velora.providers`;
  quien llama a `generate()` nunca ve un tipo de excepción de
  `anthropic`. Requiere el extra opcional `velora[anthropic]` — no es
  una dependencia obligatoria de `velora`.

## Dependencias entre componentes

```
velora.cli  →  velora.runtime
velora.cli  →  velora.configuration
velora.cli  →  velora.logging  →  velora.runtime
velora.cli  →  velora.services
velora.providers.text_generation  →  velora.runtime   (solo para LifecycleComponent)
velora.providers.text_generation  →  velora.providers  (jerarquía de error)
velora.providers.text_generation._anthropic  →  anthropic (extra opcional)
```

`velora.providers` (raíz y dominios) no es consumido todavía por
`velora.cli` ni por ningún Service — no hay Service de capacidad
(ADR-0008) que lo use aún. Es infraestructura real, completa y probada,
sin consumidor final todavía, igual que `Runtime` en PR-002 no tenía
ningún `LifecycleComponent` concreto hasta este mismo PR.

## Lo que no existe todavía

Engines, Workflows, Extensions. Tampoco existen Services de capacidad
(`NarrationService`, etc. — ahora desbloqueados por este PR, ver
ADR-0008) ni Providers de ningún otro dominio (voz, imagen, video,
música, traducción). Cualquier mención a esas capas en otros documentos
es planificación, no arquitectura vigente. Este documento se actualizará
en cada PR que introduzca una capa o dominio nuevo.
