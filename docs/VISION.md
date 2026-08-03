> **Nota de reconciliación arquitectónica.** Este documento es la visión
> de producto — el "para qué" de Velora — y es la fuente de verdad sobre
> el dominio (producción audiovisual con IA). No es `architecture.md`
> (que describe solo lo ya construido) ni sustituye a los ADR (que
> registran decisiones). Una discrepancia real fue detectada y resuelta
> al incorporar este documento: el diagrama de capas de aquí abajo dice
> `Engines → Services → Providers` (Services depende de Providers),
> mientras que el AGENT.md original decía `Providers → Services`
> (dirección contraria). Se adoptó la dirección de este documento — ver
> **ADR-0008** para la resolución completa y el diagrama de capas
> canónico vigente, que también integra Configuration y Logging
> (ausentes del diagrama de abajo, pero ya construidos y documentados en
> `architecture.md`).
>
> Este documento puede quedar desactualizado en detalles de producto
> (proveedores concretos mencionados, ejemplos de CLI futuros, etc.); lo
> que es vinculante arquitectónicamente se resuelve siempre vía ADR, no
> vía este documento.

---

# Velora — Visión General del Proyecto

## ¿Qué es Velora?

**Velora** es una plataforma de automatización para la producción de contenido audiovisual impulsada por inteligencia artificial.

Su objetivo no es únicamente generar videos, sino convertirse en un **motor de producción multimedia** capaz de transformar una idea en un producto listo para ser publicado, utilizando una arquitectura modular que permita integrar cualquier proveedor de IA, motor de render, plataforma de publicación o servicio externo sin modificar el núcleo del sistema.

En otras palabras:

> Velora es un sistema operativo para la creación de contenido.

No está diseñado para un único flujo de trabajo ni para una sola IA. Está diseñado para que cualquier flujo pueda construirse sobre él.

---

# El problema que resuelve

Actualmente la creación de contenido implica decenas de tareas manuales:

* investigar un tema
* escribir un guion
* dividir el guion por escenas
* generar narraciones
* crear imágenes
* buscar videos
* crear música
* editar
* sincronizar audio
* insertar subtítulos
* exportar
* publicar
* generar títulos
* generar descripciones
* crear miniaturas

Todo esto consume mucho más tiempo que la propia creatividad.

Velora elimina esa carga automatizando el proceso completo.

El usuario únicamente define qué quiere crear.

El sistema se encarga del resto.

---

# Filosofía

Velora no gira alrededor de una IA.

No gira alrededor de un proveedor.

No gira alrededor de una API.

Gira alrededor de un concepto:

> Todo servicio puede cambiar.

Por eso toda la arquitectura está desacoplada.

Hoy puede utilizar OpenAI.

Mañana Claude.

Después Gemini.

Después un modelo local.

El resto del sistema continúa funcionando exactamente igual.

---

# Objetivo principal

Convertir una idea en contenido terminado mediante una cadena completamente automatizada.

Ejemplo:

```
Tema

↓

Investigación

↓

Guion

↓

Storyboard

↓

Narración

↓

Imágenes

↓

Videos

↓

Música

↓

Proyecto de edición

↓

Render

↓

Publicación

↓

Estadísticas
```

Cada bloque es independiente.

Cada bloque puede reemplazarse.

---

# Arquitectura General

Velora está dividido en capas.

```
CLI

↓

Runtime

↓

Workflow Engine

↓

Engines

↓

Services

↓

Providers

↓

External APIs
```

Cada capa tiene una responsabilidad específica.

---

# Runtime

El Runtime es el corazón del sistema.

Se encarga de:

* iniciar la aplicación
* cargar configuración
* cargar plugins
* registrar servicios
* crear el contenedor de dependencias
* manejar eventos
* inicializar logging
* administrar el ciclo de vida

Nada funciona fuera del Runtime.

---

# Configuration System

Toda la configuración vive fuera del código.

Nada está "hardcodeado".

Ejemplos:

* modelos IA
* rutas
* formatos
* resolución
* proveedores
* idiomas
* voces
* estilos
* calidad
* render

Todo puede modificarse mediante archivos de configuración.

---

# Logging

Velora registra absolutamente todo.

Cada paso produce información útil para:

* depuración
* auditoría
* monitoreo
* rendimiento
* errores

No existen errores silenciosos.

---

# Dependency Injection

Todos los componentes reciben sus dependencias.

Nunca las crean.

Ejemplo:

Incorrecto

```
ImageService()

crea

OpenAIClient()
```

Correcto

```
OpenAIClient

↓

ImageService

↓

Workflow
```

Esto permite reemplazar cualquier implementación.

---

# Providers

Los Providers son adaptadores hacia servicios externos.

Por ejemplo:

## IA

* OpenAI
* Anthropic
* Gemini
* Ollama
* LM Studio

## Voz

* Voicebox
* ElevenLabs
* XTTS
* Piper

## Imágenes

* Flux
* Stable Diffusion
* MidJourney (si existiera API)
* DALL·E

## Video

* Runway
* Kling
* Pika
* Luma

## Música

* Suno
* Udio

## Traducción

* DeepL
* Google Translate

Todos implementan la misma interfaz.

El sistema nunca conoce el proveedor.

Solo conoce el contrato.

---

# Services

Los Services representan capacidades del sistema.

No representan APIs.

Ejemplo:

```
Narration Service
```

Puede usar:

* GPT
* Claude
* Gemini

Sin cambiar el resto del proyecto.

Otro ejemplo:

```
Image Service
```

Puede trabajar con:

* Flux
* SDXL
* OpenAI Images

El Workflow nunca necesita saber cuál usa.

---

# Engines

Los Engines ejecutan lógica compleja.

Ejemplos:

Story Engine

Construye la historia.

Subtitle Engine

Genera subtítulos.

Timeline Engine

Organiza escenas.

Render Engine

Construye el proyecto final.

Publish Engine

Publica contenido.

---

# Workflows

Los Workflows conectan todos los motores.

Ejemplo:

```
Crear documental
```

1. investigar

↓

2. escribir

↓

3. dividir escenas

↓

4. generar voz

↓

5. generar imágenes

↓

6. construir timeline

↓

7. renderizar

↓

8. publicar

Otro Workflow podría generar un Reel.

Otro un podcast.

Otro un video largo.

Otro únicamente audio.

El núcleo no cambia.

---

# Plugins

Velora fue diseñado para crecer.

Los plugins podrán agregar:

* nuevos proveedores
* nuevos motores
* nuevos estilos
* nuevos workflows
* nuevas integraciones

Sin modificar el Core.

---

# CLI

La interfaz de línea de comandos es la puerta de entrada.

Ejemplos futuros:

```
velora create documentary

velora create short

velora create podcast

velora render

velora publish

velora provider list

velora workflow run

velora config validate
```

Toda la funcionalidad será accesible desde la CLI y, en el futuro, podrá ser reutilizada por interfaces gráficas o servicios web.

---

# Estilos de contenido

Velora no genera únicamente videos.

Genera distintos tipos de contenido.

Ejemplos:

* Shorts
* Reels
* TikTok
* Documentales
* Videos largos
* Podcasts
* Audiolibros
* Cursos
* Presentaciones
* Contenido educativo
* Turismo
* Marketing
* Contenido corporativo

Cada uno es simplemente un Workflow diferente.

---

# Publicación

Velora también contempla la distribución del contenido.

Dependiendo del Workflow podrá generar automáticamente:

* títulos
* descripciones
* hashtags
* miniaturas
* capítulos
* subtítulos
* metadatos

Y publicar en plataformas como:

* YouTube
* Facebook
* TikTok
* Instagram
* otras plataformas mediante nuevos proveedores.

---

# Escalabilidad

Uno de los objetivos principales es que Velora pueda ejecutarse tanto en un equipo personal como en una infraestructura distribuida.

El mismo proyecto debe poder funcionar en escenarios como:

* un desarrollador creando contenido desde su computadora;
* un estudio con varios artistas y editores;
* una granja de render con múltiples nodos;
* una plataforma SaaS que procese cientos de proyectos en paralelo.

La arquitectura desacoplada facilita distribuir cargas de trabajo y sustituir componentes sin reescribir el sistema.

---

# Principios de Ingeniería

Todo el proyecto sigue una serie de principios definidos desde su diseño:

* **Runtime First**: toda la aplicación se construye alrededor del Runtime.
* **Dependency Injection**: las dependencias se inyectan, no se crean internamente.
* **Composition over Inheritance**: se favorece la composición para lograr mayor flexibilidad.
* **Stable Core**: el núcleo cambia lo menos posible; las extensiones viven fuera de él.
* **Typed Everything**: todas las interfaces y contratos están tipados.
* **Configuration over Code**: el comportamiento se define mediante configuración y no mediante cambios en el código.
* **Architecture Decision Records (ADR)**: toda decisión importante queda documentada para preservar el conocimiento del proyecto.

---

# Estado actual del proyecto

Velora se encuentra en la construcción de su **Foundation**, donde se establece la infraestructura técnica sobre la que crecerá el resto del sistema. Esta etapa incluye el Runtime, la configuración, el sistema de logging, la inyección de dependencias, los contratos principales y la estructura del proyecto. El objetivo es garantizar una base sólida, mantenible y extensible antes de implementar funcionalidades específicas.

---

# Visión a largo plazo

La ambición de Velora va más allá de automatizar la creación de videos. Busca convertirse en una plataforma universal para la orquestación de procesos creativos, donde cualquier capacidad —investigación, generación de texto, voz, imágenes, video, edición, renderizado o publicación— pueda integrarse como un módulo reutilizable.

En este modelo, la inteligencia no reside en un proveedor concreto, sino en la arquitectura que coordina todos los componentes. El resultado es una plataforma preparada para evolucionar con el ecosistema de la IA, incorporar nuevas tecnologías sin rehacer el sistema y servir como base para construir herramientas creativas cada vez más complejas.
