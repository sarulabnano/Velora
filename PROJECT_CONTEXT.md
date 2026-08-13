# PROJECT_CONTEXT

Este documento resume el estado actual de Velora. No duplica los ADR ni
`docs/VISION.md`; los referencia.

## Último PR

**PR-019 — Engines: `SubtitleEngine` cronometra por duración real del
audio (`measure_duration_seconds`, vía `mutagen`), no por conteo de
palabras.**

## Milestone activa

**Engines / Workflows.** Los cuatro Engines del pipeline de ejemplo de
`docs/VISION.md` hasta "insertar subtítulos" están coordinados por
`StoryWorkflow`, y los subtítulos ahora coinciden genuinamente con la
duración del audio generado. Próxima: por decidir contigo — ver
"Próximo paso".

## Roadmap (congelado, no modificable)

```
Foundation → Runtime → Configuration → Logging → Services →
Providers → Engines → Workflows → Extensions
```

## Documento de visión

`docs/VISION.md` — visión de producto. Incorporado en PR-005.
Discrepancias con lo construido se resuelven vía ADR.

## Componentes que existen hoy

- `velora` — paquete raíz, expone `__version__`. **Cambia**: gana su
  primera dependencia base no opcional, `mutagen` (antes,
  `dependencies = []`).
- `velora.cli` — **cambia**: el texto de ayuda de `--words-per-minute`
  se actualiza para reflejar que ahora es un ritmo de reserva, no el
  método principal de cronometraje.
- `velora.runtime`, `velora.logging`, `velora.configuration` — sin
  cambios.
- `velora.services` (raíz), `velora.services.narration`,
  `velora.services.voice`, `velora.services.image` — sin cambios.
- `velora.providers` (raíz), `velora.providers.text_generation`,
  `velora.providers.voice`, `velora.providers.image` — sin cambios.
- `velora.engines.story`, `velora.engines.narration_audio`,
  `velora.engines.scene_image` — sin cambios.
- `velora.engines.subtitle` — **cambia**: `SubtitleEngine.caption()`
  ahora recibe también `audio: StoryAudio` (firma incompatible con
  PR-018, deliberado). Mide la duración real de cada `SceneAudio` vía
  `measure_duration_seconds` (nuevo, `velora.engines.subtitle._duration`,
  usa `mutagen`). `words_per_minute` pasa de ser la fuente principal de
  cronometraje a un *fallback*, usado solo cuando la duración no puede
  medirse (audio no soportado/corrupto, o sin escena de audio
  correspondiente).
- `velora.workflows.story` — **cambia**: `run()` pasa ahora `audio` a
  `SubtitleEngine.caption()`. El orden síntesis → subtitulado deja de
  ser incidental para ser una dependencia real (el subtitulado
  necesita el audio ya sintetizado); sigue sin depender de la
  ilustración.

Ver `docs/architecture.md` para el detalle de cada símbolo.

## Estado real del producto — qué se puede hacer hoy

- **Texto + audio + imágenes + subtítulos, cronometrados con precisión,
  persistido a disco**: `velora create story` produce un directorio con
  `story.txt`, `story.srt` (con tiempos que coinciden con la duración
  real de cada clip de audio generado), y un archivo de audio y uno de
  imagen por escena.
- Ya no hay una limitación de "estimación por ritmo de lectura" para el
  caso normal — solo se degrada a esa estimación si un clip de audio en
  particular no puede leerse (caso excepcional, no el flujo esperado).

## Componentes que NO existen todavía

Extensions. Tampoco más Providers/Services de ningún dominio existente,
más dominios de Provider (video, música, traducción), más Engines
(Timeline, Render, Publish — ver `docs/VISION.md`), ni más Workflows
que `StoryWorkflow`. Ningún mecanismo para reanudar o reutilizar una
ejecución anterior de `create story` desde su directorio ya guardado.

## Decisiones vigentes (ADR)

- **ADR-0001** a **ADR-0021** — ver PRs anteriores; sin cambios.
- **ADR-0022** — `SubtitleEngine.caption()` gana un segundo parámetro,
  `audio: StoryAudio`, y mide la duración real de cada escena vía
  `measure_duration_seconds` (usa `mutagen`, primera dependencia base
  no opcional del proyecto — distinta categoría que
  `anthropic`/`elevenlabs`/`openai`, que son SDKs de proveedores
  intercambiables; `mutagen` es infraestructura genérica sin vendor
  lock-in). `words_per_minute` se conserva como fallback para una
  escena sin duración medible, no como método principal — la misma
  degradación gradual que hace que los tests con "audio" falso
  (bytes de texto plano, patrón ya establecido desde PR-012) sigan
  funcionando sin cambios. El orden síntesis→subtitulado en
  `StoryWorkflow` deja de ser una elección estética para ser una
  dependencia real. Vinculante para cualquier medición futura similar:
  medir cuando sea posible, degradar con gracia cuando no, documentar
  la categoría de la dependencia nueva (vendor SDK opcional vs.
  infraestructura base) explícitamente en su ADR.

## Criterios de aceptación vigentes

Desde un repositorio limpio:

```
git clone <repo>
uv sync
uv run velora
uv run pytest
```

El Core mantiene cobertura de pruebas ≥90%; PR-019 cierra con 100%.
`velora create story` sigue requiriendo las mismas tres claves de API
que en PR-016/PR-017/PR-018 — esta medición no añade ninguna nueva ni
cambia el comportamiento observable de la CLI más allá de subtítulos
más precisos.

## Próximo paso

Con los subtítulos ya cronometrados con precisión, la limitación que
quedaba documentada explícitamente en ADR-0021 está resuelta. Caminos
razonables para `Genera PR-020`:

1. **Timeline Engine** (según `docs/VISION.md`) — el siguiente paso del
   pipeline de ejemplo: combinar texto, audio, imágenes, y subtítulos
   en una estructura temporal única, en vez de cuatro resultados
   paralelos que la CLI solo yuxtapone por convención de nombres de
   archivo.
2. **Un cuarto dominio de Provider/Service** (video, música,
   traducción) — sigue disponible.
3. **Mejoras al propio `create story`** — p. ej. reanudar ejecuciones
   fallidas, o validar que el número de escenas de audio/imágenes/
   subtítulos coincide siempre (ya lo garantiza el diseño actual, pero
   podría documentarse con una prueba de propiedad más explícita).

Mi inclinación, si preguntas: opción 1. Es el paso que el pipeline de
`docs/VISION.md` documenta a continuación, y el primero que
genuinamente necesitaría los cuatro resultados a la vez — hasta ahora,
cada Engine nuevo dependía como mucho de dos (`Story` y, desde este PR,
`StoryAudio`). Pero, como en decisiones recientes, no hay una urgencia
clara — dime hacia dónde prefieres llevarlo y sigo.
