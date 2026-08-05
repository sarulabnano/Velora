# ADR-0014: `VoiceService`, capacidad delgada sobre `VoiceProvider`

## Status

Accepted

## Context

Tras PR-010 (`velora.providers.voice`), `PROJECT_CONTEXT.md` dejaba tres
caminos: `VoiceService`, extender `StoryWorkflow`/un Engine para
sintetizar audio directamente, o un tercer dominio de Provider (imagen).
Se eligió `VoiceService` — el mismo paso intermedio que ADR-0010 ya
demostró que vale la pena dar antes de comprometerse a una decisión de
orquestación mayor: una capa delgada que desbloquea a quien la use
después (`StoryWorkflow`, un futuro Engine de audio) sin necesitar
decidir todavía *cómo* se coordina con `StoryEngine`.

`docs/VISION.md` no usa "Voice Service" como su ejemplo canónico de
Service de capacidad (usa "Narration Service"), pero el mismo párrafo lo
generaliza explícitamente: los Services "representan capacidades del
sistema... no representan APIs". Hablar es una capacidad exactamente
igual que narrar.

## Decision

Mismo patrón exacto que ADR-0010 estableció para `NarrationService` —
cada decisión de aquella ADR se reafirma aquí sin modificación:

- **Ubicación**: `velora.services.voice`, subpaquete de `velora.services`
  (no un paquete nuevo), fuera de su raíz — mismo motivo: importar la
  infraestructura (`Clock`/`IdGenerator`) nunca debe arrastrar
  `velora.providers` para quien no lo necesita.
- **Contrato delgado**: `VoiceService.speak(text: str) -> SpeechResult`.
  No decide qué voz usar (eso vive en el `VoiceProvider` inyectado,
  ADR-0013), ni acumula configuración que ningún llamador real pide
  todavía. A diferencia de `NarrationService.narrate()`, no tiene un
  parámetro de configuración por defecto (`system_prompt` no tiene
  equivalente natural en síntesis de voz) — el constructor toma
  únicamente el `VoiceProvider` inyectado.
- **Reutiliza `SpeechResult`**, no un tipo nuevo: ya es
  provider-agnóstico (vive en `velora.providers.voice`), envolverlo de
  nuevo añadiría ceremonia, no independencia del proveedor.
- **Validación mínima con `ValueError`**, no una jerarquía de error
  propia: única precondición (`text` vacío); los fallos reales de
  negocio ya están tipados en `velora.providers`.

## Consequences

- `VoiceService` es la primera pieza que un futuro Engine o Workflow
  puede depender de forma legítima sin romper el diagrama canónico de
  ADR-0008: `Engine → VoiceService → VoiceProvider → elevenlabs`. El
  Engine nunca ve `velora.providers` ni `elevenlabs`.
- Ningún Engine o Workflow existente cambia: `StoryEngine` y
  `StoryWorkflow` no saben que `VoiceService` existe todavía.
- El siguiente paso natural queda abierto otra vez, igual que tras
  ADR-0010: con dos Services de capacidad (`NarrationService`,
  `VoiceService`) ya existentes, ahora sí hay contenido genuinamente
  distinto para que `StoryWorkflow` coordine más de un paso — la
  primera vez que extenderlo (o darle a un segundo Engine algo real que
  hacer) dejaría de ser prematuro.
