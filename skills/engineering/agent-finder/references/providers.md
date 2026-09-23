# Proveedores y reapertura

Usa esta referencia solo despues de identificar una sesion. Los comandos dependen de las versiones instaladas; si la ayuda local contradice esta tabla, prevalece la ayuda local (`<comando> --help`).

## Claude Code

- Historial: `~/.claude/history.jsonl` y `~/.claude/projects/*/*.jsonl`.
- Reabrir por ID desde el proyecto: `cd -- '/ruta/proyecto' && claude --resume 'ID'`.
- Selector interactivo: `claude --resume`.

## Codex CLI

- Historial: `${CODEX_HOME:-~/.codex}/sessions/**/*.jsonl`.
- Reabrir por ID y fijar carpeta: `codex resume --cd '/ruta/proyecto' 'ID'`.
- Ver selector global: `codex resume --all`.

## Gemini / Antigravity

- Gemini CLI puede guardar chats en `~/.gemini/tmp/*/chats/*.json`.
- Antigravity conserva transcripciones bajo `~/.gemini/antigravity-cli/brain/*/.system_generated/logs/` y artefactos bajo `~/.gemini/antigravity-ide/brain/`.
- Los comandos de reapertura no son estables entre estas aplicaciones. Si la instalacion local no expone una opcion documentada de `resume`, entrega el ID y la ruta del proyecto para localizarla en el selector de la interfaz. No inventes un comando.

## Otros asistentes

`detect` puede marcar Cursor, Continue, Aider, Cline u otros por sus directorios. Solo afirma soporte de busqueda cuando el resultado indique `searchable: true`. Para una fuente detectada pero no compatible, informa su ruta y ofrece ampliar el adaptador; no busques indiscriminadamente en bases SQLite ni perfiles del navegador.
