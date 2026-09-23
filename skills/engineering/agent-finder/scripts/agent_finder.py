#!/usr/bin/env python3
"""Find local coding-agent sessions without modifying provider data."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

HOME = Path.home()
MAX_CHARS = 160_000
MAX_FIELD = 20_000
UUID_RE = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", re.I)
WORD_RE = re.compile(r"[\w@./:#-]+", re.UNICODE)
STOP = {"algo", "arreglar", "codigo", "como", "con", "cuando", "del", "desde", "donde", "el", "en", "hacer", "hice", "la", "las", "lo", "los", "para", "pero", "por", "proyecto", "que", "quiero", "se", "similar", "una", "uno", "y"}


def default_output_dir() -> Path:
    configured = os.environ.get("AGENT_FINDER_OUTPUT_DIR")
    if configured:
        return Path(configured).expanduser()
    data_home = Path(os.environ.get("XDG_DATA_HOME", str(HOME / ".local" / "share")))
    return data_home / "agent-finder" / "exports"


def source_repo_root() -> Path | None:
    for parent in Path(__file__).resolve().parents:
        if (parent / ".git").exists():
            return parent
    return None


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def write_private(result: str, requested: Path | None, agent: str, sid: str) -> Path:
    output_dir = default_output_dir() if requested is None else requested.expanduser().parent
    if requested is None:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = output_dir / f"{agent}-{sid}-{stamp}.md"
    else:
        target = requested.expanduser()
    repo = source_repo_root()
    if repo and is_within(target, repo):
        raise SystemExit(f"Refusing to write private session data inside public repository: {repo}")
    output_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".agent-finder-", dir=output_dir, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(result)
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, target)
        os.chmod(target, 0o600)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return target


def roots() -> dict[str, Path]:
    return {
        "claude": HOME / ".claude",
        "codex": Path(os.environ.get("CODEX_HOME", str(HOME / ".codex"))),
        "gemini": HOME / ".gemini",
        "cursor": HOME / ".config" / "Cursor",
        "continue": HOME / ".continue",
        "aider": HOME / ".aider.chat.history.md",
        "cline": HOME / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev",
    }


def emit(value: Any) -> None:
    json.dump(value, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def detect() -> list[dict[str, Any]]:
    out = []
    for name, path in roots().items():
        present = path.exists()
        searchable = False
        detail = "not detected"
        if present and name == "claude":
            searchable = (path / "history.jsonl").exists() or (path / "projects").exists()
            detail = "history.jsonl/projects" if searchable else "directory only"
        elif present and name == "codex":
            searchable = (path / "sessions").exists()
            detail = "sessions" if searchable else "directory only"
        elif present and name == "gemini":
            searchable = any((path / p).exists() for p in ("tmp", "antigravity-cli/brain", "antigravity-ide/brain"))
            detail = "Gemini/Antigravity histories" if searchable else "directory only"
        elif present:
            detail = "detected; adapter not implemented"
        out.append({"agent": name, "detected": present, "searchable": searchable, "path": str(path), "detail": detail})
    return out


def query_terms(text: str) -> list[str]:
    return [word.casefold() for word in WORD_RE.findall(text) if len(word) >= 3 and word.casefold() not in STOP]


def flatten_text(value: Any, depth: int = 0) -> Iterable[str]:
    if depth > 8:
        return
    if isinstance(value, str):
        if value and len(value) <= MAX_FIELD:
            yield value
    elif isinstance(value, list):
        for item in value:
            yield from flatten_text(item, depth + 1)
    elif isinstance(value, dict):
        for key, item in value.items():
            if key.casefold() not in {"thinking", "encrypted_content", "signature", "base_instructions"}:
                yield from flatten_text(item, depth + 1)


def jsonl(file: Path) -> Iterable[dict[str, Any]]:
    try:
        with file.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    value = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if isinstance(value, dict):
                    yield value
    except (OSError, PermissionError):
        return


def modified(file: Path) -> str:
    try:
        return datetime.fromtimestamp(file.stat().st_mtime, timezone.utc).isoformat()
    except OSError:
        return ""


def claude_sessions() -> Iterable[dict[str, Any]]:
    base = roots()["claude"]
    history = base / "history.jsonl"
    grouped: dict[str, dict[str, Any]] = {}
    for obj in jsonl(history):
        sid = str(obj.get("sessionId", ""))
        if not sid:
            continue
        item = grouped.setdefault(sid, {"agent": "claude", "session": sid, "project": obj.get("project", ""), "date": "", "parts": [], "source": str(history)})
        if isinstance(obj.get("display"), str):
            item["parts"].append(obj["display"])
        if obj.get("timestamp"):
            item["date"] = str(obj["timestamp"])
    yield from grouped.values()
    projects = base / "projects"
    if projects.exists():
        known = set(grouped)
        for file in projects.glob("*/*.jsonl"):
            match = UUID_RE.search(file.name)
            sid = match.group(0) if match else file.stem
            if sid not in known:
                yield {"agent": "claude", "session": sid, "project": file.parent.name, "date": modified(file), "parts": [], "source": str(file)}


def codex_sessions() -> Iterable[dict[str, Any]]:
    folder = roots()["codex"] / "sessions"
    if not folder.exists():
        return
    for file in folder.rglob("*.jsonl"):
        match = UUID_RE.search(file.name)
        item = {"agent": "codex", "session": match.group(0) if match else file.stem, "project": "", "date": modified(file), "parts": [], "source": str(file)}
        chars = 0
        for obj in jsonl(file):
            if obj.get("type") == "session_meta" and isinstance(obj.get("payload"), dict):
                payload = obj["payload"]
                item["session"] = str(payload.get("id") or payload.get("session_id") or item["session"])
                item["project"] = str(payload.get("cwd", ""))
                item["date"] = str(payload.get("timestamp") or item["date"])
            if obj.get("type") == "response_item":
                payload = obj.get("payload", {})
                if isinstance(payload, dict) and payload.get("role") in {"user", "assistant"}:
                    for text in flatten_text(payload.get("content", [])):
                        item["parts"].append(text)
                        chars += len(text)
                        if chars >= MAX_CHARS:
                            break
            if chars >= MAX_CHARS:
                break
        yield item


def gemini_sessions() -> Iterable[dict[str, Any]]:
    base = roots()["gemini"]
    seen: set[str] = set()
    patterns = ("tmp/*/chats/*.json", "antigravity-cli/brain/*/.system_generated/logs/transcript.jsonl", "antigravity-ide/brain/*/.system_generated/logs/transcript.jsonl")
    for pattern in patterns:
        for file in base.glob(pattern):
            sid = next((part for part in file.parts if UUID_RE.fullmatch(part)), file.stem)
            if sid in seen:
                continue
            seen.add(sid)
            parts: list[str] = []
            project = ""
            chars = 0
            if file.suffix == ".jsonl":
                objects: Iterable[dict[str, Any]] = jsonl(file)
            else:
                try:
                    raw = json.loads(file.read_text(encoding="utf-8", errors="replace"))
                    objects = [raw] if isinstance(raw, dict) else [x for x in raw if isinstance(x, dict)]
                except (OSError, json.JSONDecodeError, TypeError):
                    objects = []
            for obj in objects:
                for text in flatten_text(obj):
                    if not project and text.startswith("/") and len(text) < 500:
                        project = text
                    parts.append(text)
                    chars += len(text)
                    if chars >= MAX_CHARS:
                        break
                if chars >= MAX_CHARS:
                    break
            yield {"agent": "gemini", "session": sid, "project": project, "date": modified(file), "parts": parts, "source": str(file)}


def sessions(agent: str | None = None) -> Iterable[dict[str, Any]]:
    providers = {"claude": claude_sessions, "codex": codex_sessions, "gemini": gemini_sessions}
    for name in ([agent] if agent else providers):
        if name not in providers:
            raise SystemExit(f"Unsupported agent: {name}")
        yield from providers[name]()


def rank(item: dict[str, Any], query: list[str], project: str | None) -> tuple[float, str]:
    project_text = str(item.get("project", "")).casefold()
    source = str(item.get("source", "")).casefold()
    body = "\n".join(item.get("parts", [])).casefold()
    points = 0.0
    hits: list[int] = []
    for term in query:
        count = min(body.count(term), 8)
        if count:
            points += 2 + count * 0.35
            hits.append(body.find(term))
        if term in project_text or term in source:
            points += 2.5
    if project:
        wanted = project.casefold().rstrip("/")
        if wanted in project_text or wanted in source or Path(wanted).name in project_text or Path(wanted).name in source:
            points += 7
        else:
            points -= 3
    evidence = ""
    if hits:
        pos = min(hits)
        evidence = re.sub(r"\s+", " ", body[max(0, pos - 90):pos + 230]).strip()
    return points, evidence


def search(text: str, project: str | None, agent: str | None, limit: int) -> list[dict[str, Any]]:
    terms = query_terms(text)
    if not terms:
        raise SystemExit("Query has no distinctive searchable terms")
    found = []
    for item in sessions(agent):
        points, evidence = rank(item, terms, project)
        if points > 0:
            found.append({key: item[key] for key in ("agent", "session", "project", "date", "source")} | {"score": round(points, 2), "evidence": evidence})
    found.sort(key=lambda row: (row["score"], row["date"]), reverse=True)
    return found[:limit]


def extract(agent: str, sid: str) -> str:
    for item in sessions(agent):
        if item["session"] == sid or sid in item["source"]:
            parts = list(item.get("parts", []))
            source = item["source"]
            # Claude's compact history is ideal for search, but the project JSONL
            # contains the actual conversation needed for a handoff.
            if agent == "claude":
                detailed = next((p for p in (roots()["claude"] / "projects").glob(f"*/{item['session']}.jsonl")), None)
                if detailed:
                    parts = []
                    chars = 0
                    for obj in jsonl(detailed):
                        for text in flatten_text(obj.get("message", obj)):
                            parts.append(text)
                            chars += len(text)
                            if chars >= MAX_CHARS:
                                break
                        if chars >= MAX_CHARS:
                            break
                    source = str(detailed)
            header = f"# Session handoff source\n\n- Agent: {item['agent']}\n- Session: {item['session']}\n- Project: {item['project']}\n- Date: {item['date']}\n- Source: {source}\n\n## Normalized conversation\n\n"
            chunks, total = [], 0
            for part in parts:
                clean = re.sub(r"\s+", " ", part).strip()
                if not clean or total >= MAX_CHARS:
                    continue
                chunks.append(clean[: MAX_CHARS - total])
                total += len(chunks[-1])
            return header + "\n\n".join(chunks)
    raise SystemExit(f"Session not found for {agent}: {sid}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("detect")
    find = sub.add_parser("search")
    find.add_argument("query")
    find.add_argument("--project")
    find.add_argument("--agent", choices=("claude", "codex", "gemini"))
    find.add_argument("--limit", type=int, default=8)
    show = sub.add_parser("extract")
    show.add_argument("--agent", required=True, choices=("claude", "codex", "gemini"))
    show.add_argument("--session", required=True)
    show.add_argument("--output", type=Path)
    show.add_argument("--stdout", action="store_true", help="Print instead of storing a private export")
    args = parser.parse_args()
    if args.command == "detect":
        emit(detect())
    elif args.command == "search":
        emit(search(args.query, args.project, args.agent, max(1, args.limit)))
    else:
        result = extract(args.agent, args.session)
        if args.stdout:
            print(result)
        else:
            output = write_private(result, args.output, args.agent, args.session)
            emit({"output": str(output), "chars": len(result), "mode": "0600"})


if __name__ == "__main__":
    main()
