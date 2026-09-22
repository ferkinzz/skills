#!/usr/bin/env python3
"""
Busca en index.json (generado por index_projects.py) los componentes/funciones
mas relevantes para una consulta en lenguaje natural.

Uso:
    python3 search_index.py "date picker con rango de fechas" [--top 5]
"""
import json
import os
import re
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(SKILL_DIR, "index.json")

STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "para",
    "por", "con", "en", "y", "o", "que", "se", "es", "ya", "algo", "como",
    "hice", "tengo", "busca", "un", "componente", "the", "a", "an", "for",
    "with", "of", "to", "did", "have", "already",
}

WORD_RE = re.compile(r"[a-zA-Z0-9_]+")


def tokenize(text):
    words = WORD_RE.findall(text.lower())
    # separa camelCase / PascalCase (ej. DatePicker -> date, picker)
    expanded = []
    for w in words:
        parts = re.findall(r"[a-z0-9]+|[A-Z][a-z0-9]*", w)
        expanded.extend(p.lower() for p in parts if p)
        expanded.append(w)
    return [w for w in expanded if w and w not in STOPWORDS and len(w) > 1]


def matches(query_token, field_tokens, weight):
    """Puntua un token de la consulta contra los tokens de un campo.

    Da el peso completo en match exacto, y una fraccion en match parcial
    (uno contiene al otro, ej. "upload" en "uploader" o "uploadtor2") para
    no perder variantes/plurales/conjugaciones (upload/uploader, subir/subida).
    """
    if query_token in field_tokens:
        return weight
    for ft in field_tokens:
        if len(query_token) >= 4 and len(ft) >= 4 and (query_token in ft or ft in query_token):
            return weight * 0.5
    return 0


def score_entry(tokens, entry):
    name_tokens = tokenize(entry.get("name", ""))
    desc_tokens = tokenize(entry.get("description", ""))
    path_tokens = tokenize(entry.get("rel_path", ""))
    project_tokens = tokenize(entry.get("project", ""))
    snippet_tokens = tokenize(entry.get("snippet", ""))

    score = 0.0
    for t in tokens:
        score += matches(t, name_tokens, 5)
        score += matches(t, desc_tokens, 3)
        score += matches(t, path_tokens, 2)
        score += matches(t, project_tokens, 1)
        score += matches(t, snippet_tokens, 1)
    return score


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "falta la consulta"}))
        sys.exit(1)

    query = sys.argv[1]
    top_n = 6
    if "--top" in sys.argv:
        try:
            top_n = int(sys.argv[sys.argv.index("--top") + 1])
        except (ValueError, IndexError):
            pass

    if not os.path.exists(INDEX_PATH):
        print(json.dumps({
            "ok": False,
            "error": "no existe index.json todavia, corre primero index_projects.py",
        }))
        sys.exit(1)

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        index = json.load(f)

    tokens = tokenize(query)
    scored = []
    for entry in index.get("entries", []):
        s = score_entry(tokens, entry)
        if s > 0:
            scored.append((s, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for s, e in scored[:top_n]:
        results.append({
            "score": round(s, 1),
            "project": e["project"],
            "rel_path": e["rel_path"],
            "abs_path": e["abs_path"],
            "name": e["name"],
            "type": e["type"],
            "line": e["line"],
            "description": e.get("description", ""),
            "snippet": e["snippet"],
        })

    print(json.dumps({
        "ok": True,
        "query": query,
        "total_matches": len(scored),
        "results": results,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
