#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Descargador de audio multi-SO para tableros teatrales offline.

Usa yt-dlp + ffmpeg. Detecta el sistema operativo, avisa qué herramienta
falta según el SO, descarga cada URL con numeración automática (01, 02, ...),
convierte a mp3 y valida cada archivo con ffprobe (no lo deja pasar si está
corrupto o vacío).

Uso:
    python3 download_audio.py --dir ./audio "https://youtu.be/..." ...
    python3 download_audio.py --list urls.txt --dir ./audio

El resultado se nombra "NN - titulo.mp3" en orden de uso.
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys

# Numeración por orden de uso (00, 01, ...) con el título original del medio.
OUT_TEMPLATE = "%(autonumber)02d - %(title)s.%(ext)s"


def detect_os() -> str:
    return platform.system()  # "Linux", "Darwin", "Windows"


def tool_available(tool: str) -> bool:
    return shutil.which(tool) is not None


def install_hint(os_name: str, tool: str) -> str:
    if os_name == "Linux":
        if tool == "yt-dlp":
            return "sudo apt install yt-dlp  (o: pip install yt-dlp)"
        if tool == "ffmpeg":
            return "sudo apt install ffmpeg  (incluye ffprobe)"
    elif os_name == "Darwin":
        if tool == "yt-dlp":
            return "brew install yt-dlp"
        if tool == "ffmpeg":
            return "brew install ffmpeg"
    elif os_name == "Windows":
        if tool == "yt-dlp":
            return "winget install yt-dlp  (o: pip install yt-dlp)"
        if tool == "ffmpeg":
            return "winget install ffmpeg  (o: https://ffmpeg.org/download.html)"
    return f"instala {tool} en tu sistema"


def check_tools() -> bool:
    os_name = detect_os()
    ok = True
    for tool in ("yt-dlp", "ffmpeg", "ffprobe"):
        if not tool_available(tool):
            print(f"[FALTA] {tool} no está instalado.")
            print(f"        En {os_name}: {install_hint(os_name, tool)}")
            ok = False
    return ok


def validate_audio(path: str) -> tuple[bool, str]:
    """Devuelve (ok, razon). ffprobe: stream de audio + duración > 0."""
    if not os.path.exists(path):
        return False, "el archivo no existe"
    if os.path.getsize(path) == 0:
        return False, "el archivo está vacío (0 bytes)"
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
             path],
            capture_output=True, text=True, timeout=120,
        ).stdout.strip()
        # + comprobar al menos un stream de audio
        streams = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=codec_type",
             "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=120,
        ).stdout.strip()
        if "audio" not in streams:
            return False, "sin stream de audio"
        try:
            dur = float(out)
        except ValueError:
            return False, "duración no legible"
        if dur <= 0 and streams:
            return False, "duración 0 (posible archivo corrupto)"
        return True, f"ok ({dur:.1f}s)"
    except FileNotFoundError:
        return False, "ffprobe no disponible"
    except Exception as exc:
        return False, f"error ffprobe: {exc}"


def download(url: str, out_dir: str, number: int) -> tuple[str, bool, str]:
    """Descarga una URL. Devuelve (archivo, ok, detalle)."""
    os.makedirs(out_dir, exist_ok=True)
    cmd = [
        "yt-dlp",
        "-x",                        # extraer audio
        "--audio-format", "mp3",     # formato del tablero
        "--audio-quality", "0",      # mejor calidad
        "--embed-metadata",
        "--no-playlist",
        "--autonumber-start", str(number),
        "--autonumber-size", "2",
        "-o", os.path.join(out_dir, OUT_TEMPLATE),
        "--newline",
    ]
    try:
        result = subprocess.run(cmd + [url], timeout=1800)
    except FileNotFoundError:
        return url, False, "yt-dlp no disponible"
    except Exception as exc:
        return url, False, f"error: {exc}"

    if result.returncode != 0:
        return url, False, f"yt-dlp terminó con código {result.returncode}"

    # localizar el archivo descargado (el que coincida con el número)
    matches = [f for f in os.listdir(out_dir)
               if f.startswith(f"{number:02d} - ") and f.endswith(".mp3")]
    if not matches:
        return url, False, "no encontré el mp3 descargado"
    path = os.path.join(out_dir, sorted(matches)[-1])
    ok, detail = validate_audio(path)
    return path, ok, detail


def parse_urls(args) -> list[str]:
    urls = list(args.urls)
    if args.list:
        for line in args.list:
            line = line.strip()
            if line:
                urls.append(line)
    return urls


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Descarga audios (mp3) numerados para tablero teatral.")
    ap.add_argument("urls", nargs="*", help="URLs a descargar")
    ap.add_argument("--dir", default="audio",
                    help="carpeta de salida (default: audio/)")
    ap.add_argument("--list", default=None,
                    help="archivo con una URL por línea")
    args = ap.parse_args()

    urls = parse_urls(args)
    if not urls:
        ap.error("no diste URLs (posición) ni --list")

    print(f"SO detectado: {detect_os()}")
    if not check_tools():
        print("\nResuelve las herramientas faltantes y vuelve a correr.")
        return 1

    print(f"Descargando {len(urls)} audio(s) a '{args.dir}/'...")
    failed = 0
    results = []
    for i, url in enumerate(urls, start=1):
        path, ok, detail = download(url, args.dir, i)
        status = "OK " if ok else "FAIL"
        print(f"[{status}] {i:02d}  {path if ok else url}  -> {detail}")
        if not ok:
            failed += 1
        results.append((path, ok, detail))

    if failed:
        print(f"\n{failed}/{len(urls)} fallaron. Corrige y descarga de nuevo.")
        return 1
    print(f"\nListo: {len(urls)} audio(s) validado(s) en '{args.dir}/'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())