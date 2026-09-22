#!/usr/bin/env python3
"""
Indexador incremental para la skill reuse-finder.

Recorre la carpeta raiz configurada en config.json, detecta "componentes"
reutilizables (funciones, componentes React, hooks, clases CSS, keyframes,
bloques HTML marcados) y guarda un catalogo en index.json.

Es incremental: si un archivo no cambio su mtime desde la ultima corrida,
reusa las entradas ya guardadas en vez de re-parsearlo. Los archivos borrados
se eliminan del indice automaticamente.

Uso:
    python3 index_projects.py            -> actualiza el indice (incremental)
    python3 index_projects.py --full      -> fuerza re-escaneo completo
"""
import json
import os
import re
import sys
import time

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(SKILL_DIR, "config.json")
INDEX_PATH = os.path.join(SKILL_DIR, "index.json")

JS_PATTERNS = [
    (re.compile(r'^\s*export\s+default\s+function\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\('), "export-default-function"),
    (re.compile(r'^\s*export\s+function\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\('), "export-function"),
    (re.compile(r'^\s*export\s+const\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?:async\s*)?\('), "export-const-fn"),
    (re.compile(r'^\s*export\s+class\s+([A-Za-z_$][A-Za-z0-9_$]*)'), "export-class"),
    (re.compile(r'^\s*function\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\('), "function"),
    (re.compile(r'^\s*const\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?:async\s*)?\('), "const-fn"),
    (re.compile(r'^\s*class\s+([A-Za-z_$][A-Za-z0-9_$]*)'), "class"),
]
HTML_COMMENT_COMPONENT = re.compile(r'<!--\s*component:\s*(.+?)\s*-->', re.IGNORECASE)
CSS_CLASS = re.compile(r'^\s*\.([a-zA-Z0-9_-]+)\s*(?:,|\{)')
CSS_KEYFRAMES = re.compile(r'@keyframes\s+([a-zA-Z0-9_-]+)')
LEADING_COMMENT = re.compile(r'^\s*(//|/\*|\*|<!--)')


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_old_index():
    if os.path.exists(INDEX_PATH):
        try:
            with open(INDEX_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def should_skip_dir(dirname, exclude_dirs):
    if dirname in exclude_dirs:
        return True
    if dirname.startswith(".") and dirname not in (".",):
        # cualquier carpeta oculta se salta salvo que este explicitamente permitida
        return True
    return False


def should_skip_file(filename, patterns):
    return any(p in filename for p in patterns)


def project_name_for(path, root):
    rel = os.path.relpath(path, root)
    parts = rel.split(os.sep)
    return parts[0] if parts else rel


def classify_js(name, kind, file_ext):
    is_react_ext = file_ext in (".jsx", ".tsx")
    starts_upper = name[:1].isupper()
    if name.startswith("use") and len(name) > 3 and name[3:4].isupper():
        return "hook"
    if is_react_ext and starts_upper:
        return "react-component"
    if kind in ("export-class", "class"):
        return "class"
    return "function"


def extract_leading_comment(lines, idx):
    """Busca 1-3 lineas de comentario justo arriba de la linea idx (0-based)."""
    j = idx - 1
    collected = []
    while j >= 0 and len(collected) < 3:
        line = lines[j].strip()
        if not line:
            break
        if LEADING_COMMENT.match(line) or line.endswith("*/") or line.startswith("*"):
            collected.insert(0, line)
            j -= 1
            continue
        break
    return " ".join(collected).strip()


def snippet_for(lines, idx, max_lines=14):
    end = min(len(lines), idx + max_lines)
    return "\n".join(lines[idx:end])


def parse_js_like(path, rel_path, project, file_ext, mtime):
    entries = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return entries
    lines = content.splitlines()
    for i, line in enumerate(lines):
        for pattern, kind in JS_PATTERNS:
            m = pattern.match(line)
            if m:
                name = m.group(1)
                entries.append({
                    "project": project,
                    "rel_path": rel_path,
                    "abs_path": path,
                    "name": name,
                    "type": classify_js(name, kind, file_ext),
                    "line": i + 1,
                    "description": extract_leading_comment(lines, i),
                    "snippet": snippet_for(lines, i),
                    "mtime": mtime,
                })
                break
    return entries


def parse_html(path, rel_path, project, mtime):
    entries = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return entries
    lines = content.splitlines()
    for i, line in enumerate(lines):
        m = HTML_COMMENT_COMPONENT.search(line)
        if m:
            entries.append({
                "project": project,
                "rel_path": rel_path,
                "abs_path": path,
                "name": m.group(1),
                "type": "html-block",
                "line": i + 1,
                "description": "",
                "snippet": snippet_for(lines, i),
                "mtime": mtime,
            })
    # tambien detecta funciones dentro de <script> planos
    entries.extend([
        e for e in parse_js_like(path, rel_path, project, ".html", mtime)
    ])
    return entries


def parse_css(path, rel_path, project, mtime):
    entries = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return entries
    lines = content.splitlines()
    seen_classes = set()
    for i, line in enumerate(lines):
        km = CSS_KEYFRAMES.search(line)
        if km:
            entries.append({
                "project": project, "rel_path": rel_path, "abs_path": path,
                "name": km.group(1), "type": "keyframes", "line": i + 1,
                "description": extract_leading_comment(lines, i),
                "snippet": snippet_for(lines, i), "mtime": mtime,
            })
            continue
        cm = CSS_CLASS.match(line)
        if cm and cm.group(1) not in seen_classes:
            seen_classes.add(cm.group(1))
            entries.append({
                "project": project, "rel_path": rel_path, "abs_path": path,
                "name": cm.group(1), "type": "css-class", "line": i + 1,
                "description": extract_leading_comment(lines, i),
                "snippet": snippet_for(lines, i), "mtime": mtime,
            })
    return entries


def parse_file(path, rel_path, project, ext, mtime):
    if ext in (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"):
        return parse_js_like(path, rel_path, project, ext, mtime)
    if ext == ".html":
        return parse_html(path, rel_path, project, mtime)
    if ext in (".css", ".scss"):
        return parse_css(path, rel_path, project, mtime)
    return []


def main():
    force_full = "--full" in sys.argv
    cfg = load_config()
    root = cfg["root"]
    exclude_dirs = set(cfg["exclude_dirs"])
    extensions = set(cfg["extensions"])
    exclude_patterns = cfg.get("exclude_filename_patterns", [])
    max_size = cfg.get("max_file_size_bytes", 400000)

    old = None if force_full else load_old_index()
    old_files = {}
    if old:
        # arranca con el mapa mtime x archivo guardado explicitamente (cubre
        # tambien archivos sin ninguna entrada detectada)
        for abs_path, mtime in old.get("file_mtimes", {}).items():
            old_files[abs_path] = {"mtime": mtime, "entries": []}
        for e in old.get("entries", []):
            old_files.setdefault(e["abs_path"], {"mtime": e["mtime"], "entries": []})
            old_files[e["abs_path"]]["entries"].append(e)

    new_entries = []
    file_mtimes = {}
    scanned = 0
    reused = 0
    reparsed = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d, exclude_dirs)]
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in extensions:
                continue
            if should_skip_file(fname, exclude_patterns):
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                st = os.stat(fpath)
            except OSError:
                continue
            if st.st_size > max_size:
                continue
            scanned += 1
            rel_path = os.path.relpath(fpath, root)
            project = project_name_for(fpath, root)

            cached = old_files.get(fpath)
            if cached and abs(cached["mtime"] - st.st_mtime) < 1:
                new_entries.extend(cached["entries"])
                file_mtimes[fpath] = st.st_mtime
                reused += 1
                continue

            reparsed += 1
            file_mtimes[fpath] = st.st_mtime
            new_entries.extend(parse_file(fpath, rel_path, project, ext, st.st_mtime))

    index = {
        "root": root,
        "generated_at": time.time(),
        "files_scanned": scanned,
        "files_reused": reused,
        "files_reparsed": reparsed,
        "total_entries": len(new_entries),
        "file_mtimes": file_mtimes,
        "entries": new_entries,
    }
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)

    print(json.dumps({
        "ok": True,
        "files_scanned": scanned,
        "files_reused": reused,
        "files_reparsed": reparsed,
        "total_entries": len(new_entries),
        "index_path": INDEX_PATH,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
