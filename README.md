# Mis skills

Colección personal de skills para asistentes de programación. Aquí reúno instrucciones y herramientas que uso en mis proyectos para aprovechar trabajo previo y mantener una forma consistente de trabajar.

Cada skill vive en su propia carpeta, con sus instrucciones y los recursos que necesita. El catálogo crecerá conforme agregue nuevas habilidades.

<p align="center">
  <a href="https://github.com/ferkinzz">
    <img src="assets/fernando.png" alt="Fernando — ferkinzz" width="180">
  </a>
</p>

<p align="center">
  <img src="assets/ferkinzz-signature-dark.png#gh-dark-mode-only" alt="ferkinzz" width="320">
  <img src="assets/ferkinzz-signature.png#gh-light-mode-only" alt="ferkinzz" width="320">
</p>

<p align="center">
  <a href="https://github.com/ferkinzz">github.com/ferkinzz</a> ·
  <a href="https://rtsi.site">rtsi.site</a> ·
  <a href="https://rtsi.mx">rtsi.mx</a>
</p>

## Dale este prompt a tu IA

Copia este prompt en tu asistente de programación con acceso a internet y a tus archivos. Cambia `[nombre-de-la-skill]` por la skill que quieras instalar, por ejemplo `reuse-finder`.

```text
Quiero instalar la skill [nombre-de-la-skill] de este repositorio:
https://github.com/ferkinzz/skills

Lee el README para localizarla y revisa su SKILL.md y sus archivos de apoyo.
Instala su carpeta completa en el directorio de skills correspondiente al
asistente que estoy usando, siguiendo sus convenciones de instalación.
Si no puedes identificar el asistente o necesitas elegir entre una
instalación global y una exclusiva de este proyecto, pregúntame.

Revisa los requisitos y adapta las rutas y la configuración de la copia
instalada a mi entorno. Pregúntame por los datos que no puedas deducir,
como la carpeta donde guardo mis proyectos. Si ya existe una instalación,
conserva mis ajustes y consulta antes de sobrescribir cambios locales.

Comprueba que los archivos y las rutas necesarias estén disponibles.
Al terminar, dime dónde quedó instalada, si falta algún paso para activarla
y dame un ejemplo concreto de cómo pedirte que la uses. Distingue lo que
verificaste de lo que no pudiste comprobar.
```

Si aún no sabes cuál elegir, dale este prompt:

```text
Explora https://github.com/ferkinzz/skills y lee su catálogo actual.
Explícame brevemente qué hace cada skill y en qué tareas me serviría.
Ayúdame a elegir según el trabajo que quiero hacer antes de instalarla.
```

## Catálogo

### Desarrollo

| Skill | Para qué sirve |
| --- | --- |
| [agent-finder](skills/engineering/agent-finder/SKILL.md) | Encuentra conversaciones de asistentes de código por proyecto o descripción, indica cómo reabrirlas y prepara un traspaso para continuar con otro agente. |
| [reuse-finder](skills/engineering/reuse-finder/SKILL.md) | Busca funciones, componentes, hooks y estilos en proyectos locales para reutilizar código que ya existe. |

### Planeación

| Skill | Para qué sirve |
| --- | --- |
| [platicador-de-proyecto](skills/planeacion/platicador-de-proyecto/SKILL.md) | Mantiene conversaciones persistentes y ramificables para explorar, cuestionar y documentar decisiones de producto, comunicación, marketing y evolución futura sin modificar la aplicación. |

### Creativa

| Skill | Para qué sirve |
| --- | --- |
| [tablero-audio-teatral](skills/creativa/tablero-audio-teatral/SKILL.md) | Monta el soporte de audio e imágenes de una obra/evento escénico: descarga audios (multi-SO), arma el guion técnico CUE y genera un tablero HTML offline con servidor local. |

## Organización

```text
skills/
├── README.md
├── .gitignore
└── skills/
    ├── engineering/
    │   ├── agent-finder/
    │   │   ├── SKILL.md
    │   │   ├── agents/
    │   │   ├── references/
    │   │   └── scripts/
    │   └── reuse-finder/
    │       ├── SKILL.md
    │       ├── config.json
    │       └── scripts/
    ├── planeacion/
    │   └── platicador-de-proyecto/
    │       ├── SKILL.md
    │       ├── agents/
    │       ├── references/
    │       └── scripts/
    └── creativa/
        └── tablero-audio-teatral/
            ├── SKILL.md
            ├── config.json
            ├── scripts/
            │   ├── download_audio.py
            │   └── serve.py
            └── references/
                └── tablero_audio.html
```

La primera carpeta `skills/` del esquema es este repositorio; la carpeta interior contiene la colección.

Las skills se agrupan por su propósito. Actualmente existen `engineering/` (desarrollo), `planeacion/` (decisiones y estrategia) y `creativa/` (contenido y artes escénicas). Se agregarán otras categorías cuando haya skills que las necesiten.

## Cómo usar esta colección

1. Busca una skill en el catálogo y lee su `SKILL.md` para conocer cuándo usarla y qué necesita.
2. Copia su carpeta completa al directorio de skills de tu asistente, conservando sus scripts y archivos de apoyo.
3. Revisa la configuración local y las rutas antes de utilizarla.

Cada skill documenta su propio flujo de uso. Los requisitos pueden variar: algunas solo contienen instrucciones y otras incluyen herramientas ejecutables.

### Configuración de reuse-finder

Necesita Python 3. Su archivo `config.json` define la carpeta de proyectos que se analizará, las exclusiones y los tipos de archivo admitidos. Actualmente conserva la configuración personal y las rutas de instalación originales de Claude; revísalas si la instalas en otra ubicación.

El índice `index.json` se genera localmente y queda fuera del control de versiones.

### Configuración de agent-finder

Necesita Python 3 y consulta en modo de solo lectura los historiales locales de los asistentes compatibles. Las búsquedas no crean archivos. Las extracciones y los resúmenes persistentes se guardan fuera de este repositorio en `${XDG_DATA_HOME:-~/.local/share}/agent-finder/exports/`; la ruta puede cambiarse con `AGENT_FINDER_OUTPUT_DIR`.

### Configuración de tablero-audio-teatral

Para obras de teatro, radioteatro, cuentacuentos o presentaciones escénicas. Parte de un guion ya armado y una lista de URLs: descarga audios (multi-SO, mp3), arma el guion técnico CUE y genera un tablero HTML offline con imágenes por cue y proyección; sirve la carpeta con un servidor local.

Necesita Python 3 y `yt-dlp` + `ffmpeg` para descargar. `config.json` define el formato de salida (mp3) y el modo de uso. **Advierte al usuario sobre copyright**: el material descargado es de uso local y no debe publicarse (subir audios/imágenes con copyright a internet puede tumbar el sitio y trae problemas legales).

## Agregar una skill

1. Crea `skills/<categoria>/<nombre-de-la-skill>/`, usando minúsculas y guiones para el nombre.
2. Añade un `SKILL.md` con el nombre, la descripción, los casos de uso y las instrucciones.
3. Incluye los scripts, referencias o recursos que necesite dentro de su carpeta.
4. Documenta sus requisitos y cualquier configuración necesaria.
5. Añade una entrada al catálogo de este README y al de su categoría.

Mantén cada skill enfocada en una tarea concreta. Evita guardar credenciales, cachés o resultados generados; usa rutas configurables cuando dependa del entorno local.
