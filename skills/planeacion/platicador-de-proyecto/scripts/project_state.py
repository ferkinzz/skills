#!/usr/bin/env python3
"""Emit a compact, read-only project fingerprint as JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Iterable


EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", ".next", ".nuxt", ".svelte-kit", ".turbo",
    ".cache", ".parcel-cache", ".venv", "venv", "node_modules", "vendor",
    "dist", "build", "coverage", "target", "__pycache__", ".platicador",
}
SENSITIVE_NAMES = {
    "credentials", "credentials.json", "service-account.json", "id_rsa",
    "id_ed25519", ".npmrc", ".pypirc",
}
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".jks", ".keystore"}
MEDIA_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".ico", ".pdf",
    ".mp3", ".wav", ".ogg", ".mp4", ".mov", ".avi", ".mkv", ".woff",
    ".woff2", ".ttf", ".otf", ".zip", ".gz", ".tar", ".7z",
}
MANIFEST_NAMES = {
    "package.json", "pyproject.toml", "requirements.txt", "Cargo.toml",
    "go.mod", "composer.json", "Gemfile", "mix.exs", "pom.xml",
    "build.gradle", "build.gradle.kts", "deno.json", "wrangler.toml",
    "vite.config.js", "vite.config.ts", "next.config.js", "next.config.mjs",
    "next.config.ts", "tsconfig.json",
}


def is_excluded(path: Path) -> bool:
    name = path.name.lower()
    return (
        name.startswith(".env")
        or name in SENSITIVE_NAMES
        or path.suffix.lower() in SENSITIVE_SUFFIXES | MEDIA_SUFFIXES
    )


def iter_files(root: Path, max_files: int) -> Iterable[Path]:
    count = 0
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
        for filename in sorted(files):
            path = Path(current) / filename
            if is_excluded(path):
                continue
            try:
                if path.is_symlink() or path.stat().st_size > 1_000_000:
                    continue
            except OSError:
                continue
            yield path
            count += 1
            if count >= max_files:
                return


def run_git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args], check=False, capture_output=True,
            text=True, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
    except OSError:
        return "unreadable"
    return digest.hexdigest()[:16]


def build_state(root: Path, max_files: int) -> dict:
    files = list(iter_files(root, max_files))
    relative = [path.relative_to(root).as_posix() for path in files]
    manifests = {
        path.relative_to(root).as_posix(): digest_file(path)
        for path in files
        if path.name in MANIFEST_NAMES
    }
    tree_hash = hashlib.sha256("\n".join(relative).encode()).hexdigest()[:16]
    status = run_git(root, "status", "--short", "--untracked-files=normal")
    return {
        "schema_version": 1,
        "root_name": root.name,
        "git": {
            "commit": run_git(root, "rev-parse", "HEAD"),
            "status": status.splitlines() if status else [],
        },
        "tree": {
            "file_count_sampled": len(relative),
            "truncated": len(relative) >= max_files,
            "path_digest": tree_hash,
        },
        "manifests": manifests,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root (default: current directory)")
    parser.add_argument("--max-files", type=int, default=5000)
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")
    print(json.dumps(build_state(root, max(1, args.max_files)), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
