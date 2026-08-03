# ADR-0009: Contratos de Provider por dominio, alcance síncrono, y dependencias opcionales

## Status

Accepted

## Context

PR-006 es el primer PR con una dependencia externa real (el SDK de
Anthropic) y el primero que necesita decidir cómo modelar "un Provider"
concretamente. `docs/VISION.md` describe seis dominios (texto/IA, voz,
imagen, video, música, traducción) con formas de entrada/salida
completamente distintas. Había que decidir: ¿un contrato `Provider`
único y genérico, o un contrato por dominio? Y, dado que ningún Provider
existía todavía: ¿debía la primera implementación real ser síncrona o
asíncrona, con o sin streaming, y cómo evitar que su dependencia de SDK
se convierta en una dependencia obligatoria de `velora` para quien no la
use?

## Decision

### Un contrato por dominio, no un `Provider` genérico

`velora.providers.text_generation` es un subpaquete propio, con su
propio `TextGenerationProvider`, `TextGenerationRequest`,
`TextGenerationResult`. No existe una clase `Provider` base genérica.
Un generador de imágenes no comparte forma de entrada/salida con un
generador de texto; forzar una interfaz común (`execute(input: Any) ->
Any`, por ejemplo) sacrificaría el tipado fuerte que el resto del
proyecto exige ("Typed Everything") a cambio de una abstracción que no
aportaría nada real. El único elemento compartido entre dominios es la
jerarquía de errores (`velora.providers._errors`), porque las categorías
de fallo (autenticación, rate limit, conexión, solicitud inválida) sí
son universales entre proveedores de IA, sea cual sea el dominio.

### Alcance: síncrono, sin streaming, deliberado y documentado

`TextGenerationProvider.generate()` es síncrono y devuelve el resultado
completo. El resto del proyecto no tiene todavía ningún modelo de
ejecución asíncrona (`Runtime` es síncrono); introducir `async` aquí
sería una expansión arquitectónica mayor sin ningún consumidor asíncrono
real que lo justifique. Streaming (resultados parciales) es una
superficie de diseño genuinamente distinta — backpressure, cancelación a
mitad de generación — que merece su propia decisión, no colarse como
detalle de esta. Ambas son extensiones aditivas futuras de
`TextGenerationProvider`, no rediseños.

### Dependencia opcional vía extras, no dependencia obligatoria

`anthropic` se declara en `[project.optional-dependencies]` como el
extra `anthropic` (`pip install velora[anthropic]`), nunca en
`dependencies`. "El sistema nunca conoce el proveedor" (VISION.md)
implica que instalar `velora` no debe arrastrar el SDK de cada proveedor
que exista — alguien que solo use un proveedor local (Ollama, LM Studio)
no necesita el SDK de Anthropic instalado. Importar
`velora.providers.text_generation._anthropic` sin el extra instalado
lanza un `ImportError` con el mensaje de instalación exacto, no un
`ModuleNotFoundError` genérico sin contexto.

### El primer `LifecycleComponent` real

`AnthropicTextGenerationProvider` implementa
`~velora.runtime.LifecycleComponent`: `start()` construye el cliente del
SDK (que abre un pool de conexiones HTTP); `stop()` lo cierra. A
diferencia de Configuration, Logging, y los Services de infraestructura
(ADR-0005, ADR-0007), este Provider sí tiene un recurso real que abrir y
cerrar — es la primera vez que el contrato `LifecycleComponent`, definido
en PR-002 y probado hasta ahora solo con componentes falsos, se ejercita
con una implementación real y no trivial.

### Sin llamadas de red reales en los tests

Ningún test de este PR llama a la API real de Anthropic (no hay
credenciales disponibles en este entorno, y no deberían serlo: un test
suite no debe depender de secretos ni de red externa para pasar). El
cliente del SDK se sustituye por un doble de prueba; las excepciones se
construyen como instancias reales de las clases del SDK
(`anthropic.AuthenticationError`, etc.), no como sustitutos genéricos,
para ejercitar exactamente las cláusulas `except` tal como están escritas.

## Consequences

- Añadir un segundo Provider de texto (OpenAI, Gemini) implica una nueva
  clase en `velora/providers/text_generation/`, sin tocar el contrato.
- Añadir un dominio nuevo (voz, imagen...) implica un subpaquete nuevo de
  `velora.providers`, reutilizando la jerarquía de errores compartida.
- El primer Service de capacidad (`NarrationService`, ADR-0008) podrá
  depender de `TextGenerationProvider` sin conocer `anthropic` en
  absoluto — ni siquiera transitivamente, porque el extra es opcional.
- Cualquier Provider futuro con un recurso real que gestionar (una
  conexión persistente, un pool, un proceso local) sigue este mismo
  patrón: implementa `LifecycleComponent`; uno que sea puramente
  stateless (una llamada HTTP por invocación sin cliente persistente) no
  necesita hacerlo — el criterio es siempre "¿hay un recurso real?", no
  "es un Provider".
