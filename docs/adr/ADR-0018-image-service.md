# ADR-0018: `ImageService`, capacidad delgada sobre `ImageProvider`

## Status

Accepted

## Context

Tras PR-014 (`velora.providers.image`, ADR-0017), `PROJECT_CONTEXT.md`
dejaba tres caminos: `ImageService`, persistir a disco el audio que
`StoryWorkflow` ya produce, o un cuarto dominio de Provider. Se eligió
`ImageService` — el mismo paso intermedio que ADR-0010 y ADR-0014 ya
demostraron que vale la pena dar antes de comprometerse a una decisión
de orquestación mayor: una capa delgada que desbloquea a quien la use
después (un futuro Engine de imagen, o `StoryWorkflow` extendido de
nuevo) sin necesitar decidir todavía *cómo* se coordina con
`StoryEngine`/`NarrationAudioEngine` — exactamente la misma secuencia
que ya se siguió para el dominio voz (Provider → Service → Engine,
PR-010→PR-011→PR-012), ahora aplicada a imagen.

`docs/VISION.md` no usa "Image Service" como su ejemplo canónico de
Service de capacidad, pero el mismo párrafo lo generaliza
explícitamente: los Services "representan capacidades del sistema...
no representan APIs". Dibujar es una capacidad exactamente igual que
narrar o hablar.

## Decision

Mismo patrón exacto que ADR-0010 (`NarrationService`) y ADR-0014
(`VoiceService`) ya establecieron — cada decisión de aquellas ADR se
reafirma aquí sin modificación:

- **Ubicación**: `velora.services.image`, subpaquete de
  `velora.services` (no un paquete nuevo), fuera de su raíz — mismo
  motivo: importar la infraestructura (`Clock`/`IdGenerator`) nunca
  debe arrastrar `velora.providers` para quien no lo necesita.
- **Contrato delgado**: `ImageService.draw(prompt: str) -> ImageResult`.
  No decide modelo, tamaño, ni calidad (eso vive en el `ImageProvider`
  inyectado, ADR-0017), ni acumula configuración que ningún llamador
  real pide todavía. Mismo motivo que `VoiceService.speak()` no tiene un
  parámetro de configuración por defecto: ni `system_prompt`
  (`NarrationService`) ni ningún equivalente tienen un análogo natural
  aquí tampoco — el constructor toma únicamente el `ImageProvider`
  inyectado.
- **Nombre del método, `draw`, no `generate`**: evita colisionar
  léxicamente con `ImageProvider.generate()` en el mismo call stack
  (`service.draw(prompt)` internamente llama a
  `provider.generate(request)`) — puramente una cuestión de legibilidad
  en el sitio de la llamada, sin ninguna diferencia semántica; ninguna
  decisión de ADR-0010 o ADR-0014 obligaba a un nombre concreto (`narrate`
  y `speak` ya son ambos distintos entre sí y de `generate`/`synthesize`
  en sus respectivos Providers).
- **Reutiliza `ImageResult`**, no un tipo nuevo: ya es
  provider-agnóstico (vive en `velora.providers.image`), envolverlo de
  nuevo añadiría ceremonia, no independencia del proveedor.
- **Validación mínima con `ValueError`**, no una jerarquía de error
  propia: única precondición (`prompt` vacío); los fallos reales de
  negocio ya están tipados en `velora.providers`.

## Consequences

- `ImageService` es la primera pieza que un futuro Engine o Workflow
  puede depender de forma legítima sin romper el diagrama canónico de
  ADR-0008: `Engine → ImageService → ImageProvider → openai`. El
  Engine nunca ve `velora.providers` ni `openai`.
- Ningún Engine, Workflow o la CLI existentes cambian: `StoryEngine`,
  `NarrationAudioEngine`, y `StoryWorkflow` no saben que `ImageService`
  existe todavía; `velora create story` no cambia su comportamiento ni
  sus requisitos.
- El siguiente paso natural queda abierto otra vez, igual que tras
  ADR-0010 y ADR-0014: con tres Services de capacidad
  (`NarrationService`, `VoiceService`, `ImageService`) ya existentes,
  ahora sí hay contenido genuinamente distinto para que un Engine de
  imagen — o `StoryWorkflow` extendido una vez más — coordine. La
  primera vez que hacerlo dejaría de ser prematuro es ahora, tal como
  ADR-0014 ya lo dejó anotado para su propio momento.
