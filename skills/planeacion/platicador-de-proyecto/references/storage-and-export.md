# Persistencia y exportación

## Estructura sugerida

```text
.platicador/
├── config.json
├── preferences.json
├── project-state.json
├── app-map.md
├── conversations.json
├── conversations/
│   └── <conversation-id>/
│       ├── conversation.json
│       ├── transcript.md
│       ├── branches/
│       │   └── <branch-id>.md
│       └── deliverables/
└── exports/
```

El directorio puede ser real o un symlink. Las rutas guardadas dentro de JSON deben ser relativas al directorio `.platicador` siempre que sea posible.

## Configuración

`config.json` registra como mínimo:

```json
{
  "schema_version": 1,
  "project_id": "identificador-estable",
  "project_name": "Nombre visible",
  "storage": { "mode": "repository", "path": ".platicador" },
  "created_at": "RFC-3339",
  "updated_at": "RFC-3339"
}
```

`storage.mode` es `repository` o `private`. No guardes una ruta personal absoluta en exportaciones portables.

## Preferencias

`preferences.json` puede contener solo valores que el usuario haya pedido recordar:

```json
{
  "schema_version": 1,
  "language": "es",
  "conversation_style": {
    "critical_intensity": "balanced",
    "detail": "adaptive",
    "question_frequency": "one_material_question_at_a_time",
    "challenge_assumptions": true,
    "look_for_contradictions": true
  }
}
```

Admite preferencias globales, del proyecto y temporales. La precedencia es temporal > proyecto > global. No eleves una preferencia temporal a persistente sin petición del usuario.

La configuración puede incluir `persistence.mode: "background-checkpoints"`. Este modo evita escrituras por turno y usa un único subagente de mantenimiento cuando la plataforma lo permita.

## Mapa e indicador de vigencia

`app-map.md` debe ser pequeño y navegable. Incluye solo secciones relevantes entre: propósito, públicos, arquitectura, rutas/páginas, componentes principales, funciones o servicios, datos e integraciones, voz/comunicación y preguntas abiertas. Enlaza a rutas de código en vez de copiarlo.

`project-state.json` es la salida de `scripts/project_state.py`. Sirve para detectar cambios desde el último mapa, no como índice semántico. Si cambió únicamente documentación irrelevante, no reindexes.

## Catálogo y conversación

`conversations.json` es un catálogo compacto con `id`, `title`, `aliases`, `status`, `active_branch`, etiquetas y fechas. Los estados recomendados son `active`, `paused`, `decided` y `archived`.

Cada `conversation.json` contiene:

```json
{
  "schema_version": 1,
  "id": "pricing-2026-09",
  "title": "Modelo de precios",
  "aliases": ["pricing"],
  "status": "active",
  "active_branch": "main",
  "branches": {
    "main": {
      "parent": null,
      "forked_from_entry": null,
      "status": "active",
      "summary": "",
      "decisions": [],
      "open_questions": [],
      "discarded_options": []
    }
  },
  "created_at": "RFC-3339",
  "updated_at": "RFC-3339"
}
```

Los nombres de archivo usan slugs seguros, pero el título conserva la redacción humana. Si un nombre coincide, pregunta si se retoma, se ramifica o se crea otro; no sobrescribas.

`transcript.md` conserva el historial cronológico con fecha, rama y hablante. Los archivos de `branches/` pueden contener vistas o notas específicas; no deben duplicar toda la transcripción.

## Protocolo del archivista

El mismo subagente realiza la exploración y la persistencia para que las operaciones de archivos no interrumpan el diálogo principal. Se reutiliza durante toda la sesión y procesa una tarea por vez.

Para una exploración recibe una pregunta concreta, rutas permitidas y exclusiones. Agrupa búsquedas y lecturas, evita archivos completos cuando bastan símbolos o fragmentos y devuelve:

```json
{
  "facts": [],
  "inferences": [],
  "relevant_paths": [],
  "map_is_stale": false,
  "open_questions": []
}
```

No vuelca salidas extensas de `rg`, `sed`, árboles o diffs al agente principal. Incluye fragmentos textuales solo cuando sean necesarios para justificar una conclusión. El agente principal usa el resumen para conversar y solicita una verificación focalizada si necesita evidencia exacta.

El agente principal conserva los cambios pendientes durante la conversación. En cada checkpoint envía al subagente `archivista_platicador` un delta, no una interpretación nueva de la charla:

```json
{
  "conversation_id": "pricing-2026-09",
  "branch_id": "main",
  "append_transcript": [],
  "summary_patch": "",
  "decisions_add": [],
  "open_questions_set": [],
  "discarded_options_add": [],
  "status": "active"
}
```

Al persistir, el archivista se limita a validar rutas, fusionar el delta, escribir de forma segura y devolver un resultado breve. No decide qué significa la conversación, no modifica la aplicación y no pregunta al usuario salvo que detecte un conflicto imposible de resolver. Los deltas de una misma rama se procesan en orden; nunca se lanzan dos escritores simultáneos sobre la misma conversación.

## Entregables

Antes de crear uno, pregunta si el usuario quiere: entregable, decisión estructurada o seguir explorando. Guarda cada entregable con metadatos mínimos: conversación, rama, estado de borrador, fecha y supuestos relevantes. Un entregable no autoriza modificar la aplicación.

## Exportación neutral JSON

El JSON portable incluye:

- `export_schema_version`, fecha e idioma;
- nombre y resumen del proyecto sin rutas privadas;
- conversación y rama seleccionadas;
- hechos, inferencias, decisiones, descartes, preguntas abiertas y próximos pasos por separado;
- entregables solicitados;
- historial solo si el usuario lo pide o resulta imprescindible.

No presentes inferencias como hechos. Elimina secretos y datos personales innecesarios.

## Exportación Markdown

Produce un documento autocontenido con:

1. propósito del traspaso;
2. contexto mínimo del proyecto;
3. papel solicitado al siguiente asistente;
4. decisiones cerradas que debe respetar;
5. tema y rama actuales;
6. hechos e inferencias claramente separados;
7. alternativas descartadas y motivos;
8. preguntas abiertas y siguiente acción esperada.

Debe poder pegarse en otra interfaz sin depender de archivos locales. No incluyas una transcripción extensa cuando un resumen fiel sea suficiente.
