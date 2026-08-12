# PROJECT_CONTEXT

Este documento resume el estado actual de Velora. No duplica los ADR ni
`docs/VISION.md`; los referencia.

## Último PR

**PR-017 — CLI: `velora create story` persiste su resultado a disco.**

## Milestone activa

**CLI / entregable de punta a punta.** El pipeline completo
(texto → audio → imágenes → disco) ya está cerrado. Próxima: por
decidir contigo — ver "Próximo paso".

## Roadmap (congelado, no modificable)

```
Foundation → Runtime → Configuration → Logging → Services →
Providers → Engines → Workflows → Extensions
```

## Documento de visión

`docs/VISION.md` — visión de producto. Incorporado en PR-005.
Discrepancias con lo construido se resuelven vía ADR.

## Componentes que existen hoy

- `velora` — paquete raíz, expone `__version__`.
- `velora.cli` — **cambia**: `create story` gana un argumento
  `--output-dir` (por defecto, `.`). Tras ejecutar `StoryWorkflow` con
  éxito, escribe un subdirectorio nuevo (nombrado con el `runtime_id`
  de esa ejecución) con: `story.txt` (transcripción), y un archivo de
  audio y uno de imagen por escena (`scene_{index:03d}.{formato}`). Un
  fallo escribiendo a disco se reporta como `fatal`, igual que
  cualquier otro fallo. La salida de stdout ahora imprime los nombres
  de archivo guardados por escena, y la ruta completa del directorio.
- `velora.runtime`, `velora.logging`, `velora.configuration` — sin
  cambios funcionales.
- `velora.services` (raíz), `velora.services.narration`,
  `velora.services.voice`, `velora.services.image` — sin cambios.
- `velora.providers` (raíz), `velora.providers.text_generation`,
  `velora.providers.voice`, `velora.providers.image` — sin cambios.
- `velora.engines.story`, `velora.engines.narration_audio`,
  `velora.engines.scene_image` — sin cambios.
- `velora.workflows.story` — sin cambios: la persistencia vive
  enteramente en `velora.cli`, no en `StoryWorkflow`.

Ver `docs/architecture.md` para el detalle de cada símbolo.

## Estado real del producto — qué se puede hacer hoy

- **Solo texto**: `StoryEngine` por sí solo. Funciona.
- **Texto + audio + imágenes, en memoria**: `StoryWorkflow` con los
  tres Engines, sin pasar por la CLI. Funciona.
- **Texto + audio + imágenes, persistido a disco**: `velora create
  story` desde la CLI (requiere las tres claves de API). **Funciona de
  punta a punta** — produce un directorio autocontenido
  (`story.txt` + un archivo de audio y uno de imagen por escena) que el
  usuario puede abrir directamente, sin ningún paso manual adicional.

## Componentes que NO existen todavía

Extensions. Tampoco más Providers de ningún dominio existente, más
dominios de Provider (video, música, traducción), más Engines
(Subtitle, Timeline, Render, Publish), ni más Workflows que
`StoryWorkflow`. Ningún mecanismo para reanudar o reutilizar una
ejecución anterior desde su directorio guardado — cada ejecución de
`create story` es independiente.

## Decisiones vigentes (ADR)

- **ADR-0001** a **ADR-0019** — ver PRs anteriores; sin cambios.
- **ADR-0020** — `create story` persiste su resultado a disco.
  `--output-dir` (por defecto `.`); cada ejecución crea un
  subdirectorio propio nombrado con el `runtime_id` que el `Runtime` de
  esa ejecución ya genera (sin inventar un segundo identificador).
  Contenido: `story.txt` (transcripción) + un archivo de audio y uno de
  imagen por escena, con índice de tres dígitos para preservar el orden
  alfabético. La persistencia vive enteramente en `velora.cli` — ningún
  Engine, Service, o Provider, ni `StoryWorkflow` mismo, saben que su
  resultado terminará en disco. Un fallo de E/S (`OSError`) se reporta
  igual que cualquier otro fallo `fatal`, antes de imprimir el resto de
  la salida. Vinculante para cualquier persistencia futura de otro
  Workflow: la misma capa (CLI), el mismo principio (todo o nada,
  reutilizar identificadores que ya existen en vez de inventar nuevos).

## Criterios de aceptación vigentes

Desde un repositorio limpio:

```
git clone <repo>
uv sync
uv run velora
uv run pytest
```

El Core mantiene cobertura de pruebas ≥90%; PR-017 cierra con 100%.
`velora create story --topic "..."` ahora escribe su resultado a disco
por defecto en el directorio actual (configurable con `--output-dir`).

## Próximo paso

Con el pipeline completo cerrado de punta a punta — texto, audio,
imágenes, y ahora persistencia — el "primer resultado tangible" que
`PROJECT_CONTEXT.md` venía posponiendo desde PR-013 ya no es un
pendiente. Quedan varios caminos razonables para `Genera PR-018`, todos
genuinamente abiertos por primera vez en muchos PRs, sin una
inclinación tan clara como en decisiones anteriores:

1. **Un Engine nuevo que dependa de `StoryAudio`/`StoryImages`** (p.
   ej. Subtitle Engine, según `docs/VISION.md`) — el pipeline documentado
   sigue con "construir timeline" y "renderizar" después de "generar
   imagenes".
2. **Un cuarto dominio de Provider/Service** (video, música,
   traducción) — sigue disponible, con el mismo patrón ya demostrado
   tres veces.
3. **Mejoras al propio `create story`** — por ejemplo, permitir
   reanudar/reintentar una ejecución fallida, o exportar en otros
   formatos — ninguna urgente, pero ahora que hay un entregable real,
   son las primeras mejoras "de producto" genuinamente posibles.

Sin inclinación fuerte de mi parte esta vez — las tres son razonables y
el pipeline ya es funcional; dime hacia dónde prefieres llevarlo y sigo.
