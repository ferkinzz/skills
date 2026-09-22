---
name: reuse-finder
description: Busca en todos los proyectos locales del usuario (carpeta raiz configurada en config.json) componentes, funciones, hooks o bloques CSS/HTML ya implementados antes, para reutilizarlos en el proyecto actual en vez de reescribirlos. Se activa cuando el usuario pregunta si ya implemento algo parecido, pide buscar un componente/funcion similar en otro proyecto, o dice frases como "ya hice algo asi", "tengo un [x] en otro proyecto", "busca en mis proyectos", "no quiero reescribir esto".
---

# reuse-finder

Encuentra y reutiliza codigo que el usuario ya escribio en alguno de sus
proyectos anteriores, en vez de reimplementarlo desde cero.

Mantiene un indice incremental (`index.json`) de "componentes reutilizables"
detectados en la carpeta raiz configurada en `config.json` (por defecto
`/home/ferkinzz/Documentos`): funciones exportadas, componentes React, custom
hooks, clases, clases CSS, `@keyframes` y bloques HTML marcados con
`<!-- component: nombre -->`.

## Cuando usar esta skill

- El usuario describe una funcionalidad y sospecha (o recuerda) que ya la
  construyo en otro proyecto.
- El usuario pide explicitamente "busca en mis proyectos algo como...".
- Antes de implementar desde cero algo con pinta de reutilizable (un
  datepicker, un uploader, un carrusel, un parser de X, un modal, animaciones
  CSS especificas, etc.) vale la pena consultar el indice primero, aunque el
  usuario no lo pida explicitamente, si el contexto sugiere que ya pudo
  haberlo hecho antes.

## Flujo

1. **Actualiza el indice (incremental, rapido).** Corre siempre esto primero,
   incluso si crees que ya esta actualizado — es barato porque solo re-parsea
   archivos cuyo mtime cambio:

   ```bash
   python3 /home/ferkinzz/.claude/skills/reuse-finder/scripts/index_projects.py
   ```

   La primera vez que se corre (o si borraron `index.json`) hace un escaneo
   completo y puede tardar unos segundos mas; las siguientes veces es casi
   instantaneo porque reusa las entradas de archivos sin cambios.

2. **Busca en el indice** con la descripcion del usuario tal cual (en
   espanol o ingles, no hace falta traducir ni resumir mucho):

   ```bash
   python3 /home/ferkinzz/.claude/skills/reuse-finder/scripts/search_index.py "descripcion de lo que busca el usuario"
   ```

   Devuelve un JSON con los candidatos mejor rankeados: `project`,
   `rel_path`, `abs_path`, `name`, `type`, `line`, `description`, `snippet`.

3. **Si no hay resultados o el score es muy bajo (<3)**, no inventes
   coincidencias. Dilo claramente y ofrece:
   - reformular la busqueda con otras palabras clave, o
   - hacer un `grep`/`Grep` en vivo mas amplio sobre el mismo root como
     respaldo puntual, o
   - proceder a implementar desde cero.

4. **Presenta 3-5 candidatos como maximo** al usuario, no el JSON crudo:
   proyecto, ruta relativa, tipo (funcion/componente/hook/css/etc.) y una
   linea de contexto (el snippet resumido, no el bloque completo). No leas ni
   pegues el archivo completo todavia.

5. **Pregunta cual usar** con la herramienta de preguntas si hay ambiguedad
   real entre 2+ candidatos razonables, o si ninguno encaja del todo bien.
   Si hay un match claramente dominante (score muy por encima del resto,
   nombre y descripcion calzan), puedes proponerlo directamente y pedir
   confirmacion en texto en vez de forzar una pregunta de opcion multiple.

6. **Una vez elegido**, usa `Read` sobre el `abs_path` (con `offset` cerca de
   `line` si el archivo es grande) para traer el codigo real completo antes
   de adaptarlo — el snippet del indice es solo un preview, puede estar
   incompleto o cortado.

7. **Adapta el codigo al proyecto actual** ajustando imports, convenciones de
   nombres, estilos (Tailwind vs CSS plano, etc.) del proyecto destino — no
   lo copies literal sin revisar que encaje con el stack donde se va a usar.

## Mantenimiento

- El root y las carpetas excluidas se configuran en `config.json` de esta
  skill. Si el usuario menciona un proyecto fuera de esa carpeta raiz, dile
  que hay que agregar esa ruta a `config.json` (o correr el indexador contra
  ella aparte).
- Si el usuario reporta que faltan resultados obvios, probable causa:
  carpeta del proyecto listada en `exclude_dirs`, extension no cubierta en
  `extensions`, o archivo mayor a `max_file_size_bytes`.
- `index_projects.py --full` fuerza un re-escaneo completo ignorando la
  cache — usalo solo si el usuario sospecha que el indice quedo corrupto o
  desincronizado, no de rutina.
