---
name: agent-finder
description: Encuentra sesiones y conversaciones pasadas de asistentes de codigo instalados localmente a partir de una carpeta, proyecto o descripcion en lenguaje natural. Usala cuando el usuario no recuerda que agente hizo un trabajo, quiere reabrir la sesion correcta o necesita resumirla para continuar con otro agente.
---

# Agent Finder

Localiza trabajo previo sin obligar al usuario a recordar el asistente, el ID de sesion ni las palabras exactas que uso. Opera sobre historiales locales y en modo de solo lectura; no abras una sesion ni escribas un traspaso en disco salvo que el usuario lo pida.

## Flujo

1. Convierte la descripcion libre del usuario en 2-6 terminos distintivos. Conserva nombres de funciones, rutas, errores, tecnologias y frases literales; elimina palabras genericas. No inventes detalles.
2. Si el usuario señala una carpeta, resuelvela a ruta absoluta. Si solo da un nombre, usa `--project` con ese nombre. La carpeta actual es una pista, no un filtro obligatorio, salvo que el usuario diga que el trabajo fue ahi.
3. Detecta fuentes disponibles:

   ```bash
   python3 scripts/agent_finder.py detect
   ```

4. Busca primero con una consulta precisa y un limite pequeno:

   ```bash
   python3 scripts/agent_finder.py search "terminos distintivos" --project "/ruta/o/nombre" --limit 8
   ```

   Omite `--project` si no hay pista de proyecto. Si los resultados son pobres, repite con sinonimos o menos terminos. No presentes coincidencias cuyo contexto no respalde la descripcion.
5. Presenta como maximo cinco opciones: asistente, fecha, proyecto/carpeta, una evidencia breve, ID de sesion y nivel de confianza. Explica si una fuente fue detectada pero no es compatible.
6. Si hay mas de una opcion razonable, pide al usuario elegir. Si hay una coincidencia claramente dominante, indicala y ofrece abrirla o preparar un traspaso.
7. Despues de elegir, extrae el contexto normalizado:

   ```bash
   python3 scripts/agent_finder.py extract --agent codex --session SESSION_ID
   ```

   La extraccion se guarda fuera del repositorio en el almacen privado descrito abajo. Lee el resultado antes de resumirlo. No pegues la transcripcion completa al usuario.

## Almacenamiento privado

- `search` y `detect` no crean archivos.
- `extract` guarda por defecto en `${XDG_DATA_HOME:-~/.local/share}/agent-finder/exports/`, crea la carpeta con permisos `0700` y el archivo con `0600`.
- `AGENT_FINDER_OUTPUT_DIR` permite cambiar el directorio privado sin editar la skill.
- `--output /ruta/archivo.md` permite elegir otro archivo, pero el script rechaza rutas dentro del repositorio que contiene esta skill.
- `--stdout` evita crear archivos; usalo cuando el agente pueda consumir la salida directamente.
- Si se genera un resumen de traspaso persistente, guardalo en el mismo directorio privado, nunca junto al codigo de esta skill ni dentro del proyecto publico, salvo una peticion posterior e inequivoca del usuario.

## Reabrir o transferir

Consulta [references/providers.md](references/providers.md) antes de dar un comando de reapertura. Usa el comando correspondiente al proveedor y la ruta del proyecto. No ejecutes el comando: abrir una sesion interactiva queda a eleccion del usuario.

Si el proveedor ya no esta disponible, la suscripcion expiro o el usuario prefiere otro agente, crea un resumen de traspaso a partir de `extract`. Incluye:

- objetivo original y estado actual;
- decisiones y restricciones relevantes;
- archivos cambiados o mencionados, sin afirmar cambios no comprobados;
- comandos o pruebas ejecutados y sus resultados conocidos;
- errores, pendientes y siguiente paso recomendado;
- ID, proveedor, proyecto y fecha de la sesion fuente.

Separa hechos observados de inferencias. Revisa el repositorio actual cuando sea necesario para confirmar que el estado no cambio desde la sesion. Excluye secretos, tokens, credenciales y bloques extensos de codigo. El resumen debe ser neutral y utilizable por cualquier agente.

## Limites y privacidad

- Busca solo en datos locales del usuario. No envies conversaciones a servicios externos ni uses busqueda web para analizar su contenido.
- No guardes transcripciones, indices, resultados o resumenes dentro del repositorio de la skill.
- No leas archivos de credenciales. El script excluye rutas conocidas de secretos y devuelve fragmentos acotados.
- Los formatos cambian entre versiones. `detect` distingue fuentes compatibles de instalaciones solamente detectadas; informa la limitacion en vez de prometer una cobertura falsa.
- Una coincidencia textual no demuestra que el trabajo se completo. Confirma con la conversacion elegida y, cuando importe, con el estado actual del proyecto.
