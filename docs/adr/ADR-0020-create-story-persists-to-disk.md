# ADR-0020: `velora create story` persiste su resultado a disco

## Status

Accepted

## Context

`PROJECT_CONTEXT.md` dejaba pendiente, desde PR-013, persistir a disco
lo que `StoryWorkflow` produce — pospuesto tres veces (PR-013, PR-014,
PR-015/PR-016) a favor de seguir horizontal primero. Con los tres
Engines ya coordinados (PR-016, ADR-0019), es el último paso que falta
para que `velora create story` produzca un resultado que sobreviva
fuera de la terminal que lo invocó: hasta ahora, la CLI solo reportaba
tamaño y formato de cada escena, sin escribir ningún archivo.

## Decision

### Ubicación: un subdirectorio nuevo por ejecución, bajo `--output-dir`

`create story` gana un argumento `--output-dir` (por defecto, `.`, el
directorio actual). Dentro de él, cada ejecución crea un subdirectorio
propio, nombrado con el `runtime_id` que el `Runtime` de esa misma
ejecución ya genera (`velora.runtime`, vía `UUIDIdGenerator`) — no se
inventa un segundo identificador: el Runtime ya produce uno único por
ejecución, y reutilizarlo evita que ejecuciones sucesivas con el mismo
`--output-dir` se pisen entre sí sin que el usuario tenga que elegir un
nombre distinto cada vez.

### Qué se guarda: transcripción + un archivo por escena, audio e imagen

Dentro del subdirectorio de la ejecución:

- `story.txt` — una transcripción con el tema y el texto de cada
  escena, el mismo contenido que la CLI ya imprime a stdout. Sin este
  archivo, el directorio de salida contendría solo binarios sin
  contexto legible; con él, es un entregable autocontenido — nadie
  necesita conservar la salida de terminal para saber qué dice cada
  escena.
- `scene_{index:03d}.{audio_format}` — el audio de cada escena
  (`NarratedStory.audio.scenes`).
- `scene_{index:03d}.{image_format}` — la imagen de cada escena
  (`NarratedStory.images.scenes`).

El índice con padding de tres dígitos (`000`, `001`, ...) garantiza que
un listado alfabético del directorio preserve el orden narrativo, sin
depender de que el sistema de archivos u otra herramienta hagan un
ordenamiento numérico correcto.

### Cuándo se escribe: después de que el Workflow completa, antes de imprimir

`_save_narrated_story` se llama después de que `workflow.run()`
devuelve con éxito, y antes de que `_run_create_story` imprima nada al
usuario — lo impreso (incluida la línea `Saved to: ...`) describe lo
que ya se escribió, nunca una promesa de lo que se escribirá. Un fallo
al persistir (`OSError`: permisos, disco lleno, etc.) se reporta con el
mismo formato `fatal` que cualquier otro fallo de este comando, y
detiene la ejecución antes de imprimir el resto de la salida — ADR-0016
ya estableció el mismo principio de "todo o nada" para el propio
`StoryWorkflow"; aquí se extiende al paso final de persistencia.

### Formato de salida: nombres de archivo, no bytes/formato

La salida de stdout cambia de `(48213 bytes, mp3)` a `audio:
scene_000.mp3` por escena — ahora que el archivo existe en disco, decir
su nombre es más útil que su tamaño: el usuario puede abrirlo
directamente desde la ruta impresa (`Saved to: ...`) sin tener que
calcular el nombre del archivo por su cuenta.

## Consequences

- `velora create story` produce, por primera vez, un resultado
  utilizable fuera de la sesión que lo invocó — cierra el pendiente que
  quedó abierto desde PR-013.
- Ningún Engine, Service, o Provider cambia: la persistencia vive
  enteramente en `velora.cli` (`_save_narrated_story`), la única capa
  que ya sabe que "disco" existe como destino — ni `StoryWorkflow` ni
  ningún Engine necesitan saber que su resultado terminará en un
  archivo.
- Ejecuciones sucesivas con el mismo `--output-dir` nunca se pisan: el
  `runtime_id` de cada ejecución es único por construcción
  (`UUIDIdGenerator`).
- El siguiente Engine que dependa de `StoryAudio`/`StoryImages` (p. ej.
  un Subtitle Engine) seguirá operando sobre los tipos en memoria que
  `StoryWorkflow` ya produce, no sobre los archivos que esta ADR
  persiste — la persistencia a disco es una salida de la CLI, no una
  fuente de verdad de la que el propio Workflow dependa.
