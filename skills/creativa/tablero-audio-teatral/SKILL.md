---
name: tablero-audio-teatral
description: Para proyectos teatrales, de radioteatro, cuentacuentos o presentaciones escenicas de aficionados e independientes. A partir de un guion ya armado y audios autorizados, arma el guion tecnico con CUE list, genera un tablero HTML de operacion (loop, fundidos, atajos, imagenes por cue y proyeccion) y lo sirve localmente. Solo ayuda a publicarlo cuando el usuario confirma expresamente que tiene permisos o que todo el material permite ese uso por su licencia o por estar en dominio publico.
---

# tablero-audio-teatral

Monta el soporte de audio (e imagenes) de una obra de teatro, radioteatro,
cuentacuentos o evento escenico para aficionados e independientes, todo
funcionando **sin internet** y en una **carpeta auto-contenida**: el HTML de
operacion, los audios y las imagenes viven juntos, se abren en el navegador y
se sirven con un servidor local.

La skill NO inventa la obra: el guion llega **ya armado** (dialogos, escenas,
direcciones de escena). Si faltan los cues de audio, el agente puede
**sugerirlos** (mapeo audio->escena) y el usuario los confirma.

## Advertencia legal (leer y aplicar SIEMPRE)

> Esta skill descarga sonido e imagenes de internet (p. ej. de YouTube) y los
> usa en un tablero de operacion. Ese material suele tener **copyright**.
> Bajar canciones/audios/imagenes y subirlos a un sitio publico **afecta al
> copy de las obras** y el sitio **puede ser tumbado** (DMCA/copyright
> strikes). Por eso:

1. **Advierte siempre al usuario** antes de descargar (texto corto): que un
   archivo sea gratuito o este disponible en internet no significa que este
   libre de copyright. Hay que respetar su licencia tanto en usos locales como
   al publicarlo.
2. Si el usuario pide publicar, subir, deployar o hostear el tablero (GitHub
   Pages, Netlify, Vercel, un servidor, etc.), **detente y avisa antes de
   hacerlo**: subir audios/imagenes con copyright a internet hace que la web
   se pueda caer y trae problemas legales. No lo hagas hasta que el usuario
   confirme expresamente que cada recurso es propio, esta en dominio publico,
   tiene permiso del titular o posee una licencia que permite ese uso.
3. Si el usuario confirma que puede publicar, registra titulo, autor, URL y
   licencia de cada recurso en `creditos_y_licencias.txt`, incluye las
   atribuciones requeridas y conserva una copia o captura de la licencia. Si
   no puede confirmar los derechos de un recurso, excluyelo de la publicacion.
4. Para buscar alternativas autorizadas, lee
   [references/bibliotecas-audio.md](references/bibliotecas-audio.md). Nunca
   interpretes "royalty-free" o "sin copy" como ausencia de condiciones.

## Cuando usar esta skill

- El usuario tiene un guion/obra terminada y necesita audios de fondo o de
  efectos para la puesta en escena.
- El usuario quiere un tablero de operacion de audio para su obra (botones
  que suenan en loop, se funden al cambiar, atajos de teclado).
- El usuario necesita que el tablero muestre imagenes por cue y/o proyectarlas
  en pantalla completa en un segundo monitor.

## Requisitos del entorno

La skill detecta el SO (Linux/macOS/Windows) y usa la herramienta adecuada:

- **yt-dlp** para descargar audio desde URLs.
- **ffmpeg + ffprobe** para convertir/validar el audio y conseguir mp3.

Si faltan, el agente da la instruccion de instalacion segun el SO y propone
instalarlas. No instales nada sin permiso del usuario.

El script `scripts/download_audio.py` verifica todo esto y avisa que falta.

## Flujo

### Paso 0 - Advertencia legal

Da la advertencia de copyright (seccion superior) al usuario ANTES de empezar
a descargar. Es obligatoria.

### Paso 1 - Reunir el material de entrada

El usuario debe dar:

1. **El guion ya armado** (texto: dialogos, descripciones de escena). Si solo
   trae el guion literario y no hay cues, propone un mapa de cues (sub-paso 3).
2. **La tabla de audios**: que audio va en cada cue/escena (nombre descriptivo
   + URL de descarga, p. ej. de YouTube). Si el usuario no la da pero da URLs,
   pregunta como mapearlas a las escenas.
3. **Imagenes (opcional por cue)**: el usuario las trae, o el agente propone
   placeholders, o el agente las genera si tiene capacidad. Si se descargan
   imagenes de internet, aplicar la misma advertencia de copyright. Pregunta
   siempre antes de buscar/generar imagenes: de donde salen.
4. **Destino**: uso local o publicacion. Para publicar, solicita la
   confirmacion de derechos indicada arriba antes de preparar el despliegue.

### Paso 2 - Descargar los audios

Corre el script de descarga multi-SO (detecta el SO y usa yt-dlp + ffmpeg):

```bash
python3 "<ruta-a-esta-skill>/scripts/download_audio.py" --dir ./audio \
  "https://youtu.be/..." "https://youtu.be/..." ...
```

- Numeracion automatica: `01 - Titulo.mp3`, `02 - ...` en orden de uso.
- Convierte a mp3 (formato estandar del tablero).
- **Valida cada archivo descargado** con ffprobe (duracion y stream de audio
  validos) e informa resultados. Si algo falla, te lo dice.

El script acepta tambien un archivo con una URL por linea: `--list urls.txt`.

### Paso 3 - Armar el guion tecnico (CUE list)

Con el guion del usuario y la tabla de audios, genera el guion tecnico `.txt`
con la convencion:

```text
CUE 1 - <nombre de la escena>
    Audio: <nro> - <archivo.mp3>
    Volumen: <bajo/media/alto>
    Nota: cuando entra/sale
```

Si al guion le faltan cues, proponlos (mapea audios a escenas segun el
significado del guion) y pide confirmacion al usuario.

### Paso 4 - Generar el tablero HTML offline

Usa la plantilla `references/tablero_audio.html` como base:

1. Copia la plantilla al directorio del proyecto.
2. Sustituye el bloque de CONFIG (botones de audio, seccion de imagenes,
   nombre de archivos) por el del proyecto.
3. Embebe el guion (texto) y los cues en el bloque del script del HTML.
4. Copia los audios a `audio/` y las imagenes a `img/`, dentro de la carpeta
   del proyecto, para que quede **auto-contenida**.
5. El HTML debe usar rutas relativas: `audio/<archivo.mp3>` e
   `img/<archivo.ext>`.
6. Muestra dentro de cada boton/cue una miniatura de su imagen para que el
   operador pueda identificarla antes de proyectarla. Reserva un tamano
   uniforme para evitar saltos en el tablero y marca claramente `Sin imagen`
   cuando el cue no tenga una. La miniatura debe tener texto alternativo
   descriptivo; no reemplaza el nombre escrito del cue.

El tablero ya incluye:
- Botones por audio en loop infinito con fundido al cambiar.
- Volumen global y boton "detener todo".
- Atajos de teclado (1-9 por track, espacio = detener).
- Panel de guion + cues sincronizado.
- Imagenes por cue y una **ventana/pestaña de proyeccion independiente**,
  sincronizada con el tablero por el servidor local. La vista de proyeccion
  tiene su propio boton de pantalla completa para colocarla en el segundo
  monitor; no uses una superposicion dentro de la pestaña del operador.
- Miniaturas visibles dentro de los botones del tablero para reconocer cada
  imagen antes de enviarla a proyeccion.
- Por defecto, los archivos se sirven con el servidor local (ver paso 5).

### Paso 5 - Servir localmente por defecto

Corre el servidor local incluido, que detecta el SO y abre el navegador:

```bash
python3 "<ruta-a-esta-skill>/scripts/serve.py" --dir . [--port 8000]
```

Abre `http://localhost:8000/tablero_audio.html` (o el nombre que tenga el
HTML). Recordar al usuario:

> Se abrio en localhost (solo tu maquina). No publiques la carpeta mientras
> no hayas confirmado los permisos o licencias de todos sus recursos.

### Paso 5b - Publicar (solo con confirmacion expresa)

Solo prepara o ejecuta un despliegue si el usuario confirma expresamente que
todos los audios e imagenes son propios, estan en dominio publico, cuentan con
permiso o tienen una licencia compatible con la publicacion prevista. Antes:

1. Crea `creditos_y_licencias.txt` con recurso, autor, URL, licencia y fecha de
   consulta.
2. Incluye en el tablero los creditos exigidos por las licencias.
3. Excluye cualquier recurso dudoso o sin licencia verificable.
4. Advierte que la confirmacion del usuario no elimina las condiciones de las
   licencias ni posibles reclamaciones automatizadas.

### Paso 6 - Verificar

- Abre el tablero en el navegador y confirma que cada boton reproduce su
  audio y se funde al cambiar.
- Confirma que las imagenes aparecen en su cue y en la vista de proyeccion.
- Confirma que cada cue muestra la miniatura correcta y que los cues sin
  recurso visual dicen `Sin imagen`.
- Confirma que "Abrir proyeccion" crea otra ventana/pestaña, que el tablero
  indica "Conectada" y que al cambiar de cue la imagen se actualiza sin
  recargar. Mueve esa ventana al segundo monitor y activa alli pantalla
  completa.
- Valida de nuevo con ffprobe cualquier audio que haya dado error al
  descargar.

## Estructura de la carpeta resultante

```text
mi-obra/
├── tablero_audio.html   (o "tablero_<obra>.html")
├── guion_tecnico.txt
├── creditos_y_licencias.txt (obligatorio si se publica)
├── audio/                (01 - ....mp3, 02 - ....mp3, ...)
└── img/                  (si hay imagenes: 01 - ...., ...)
```

Todo se abre en el navegador a traves del servidor local. La publicacion es
opcional y queda condicionada al Paso 5b.

## Mantenimiento

- Si el usuario reporta un audio que no suena, revisa: archivo faltante en la
  carpeta, formato distinto de mp3, origen con region bloqueada (yt-dlp).
- Si el usuario quiere otro formato diferente a mp3, ajusta la orden de
  descarga; el HTML reproduce mp3, wav, ogg, m4a segun el navegador, pero mp3
  es el mas compatible.
- Los atajos y el estilo visual del tablero se ajustan en la plantilla
  `references/tablero_audio.html`.
