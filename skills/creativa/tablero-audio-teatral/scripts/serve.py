#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Servidor local multi-SO para tableros teatrales offline.

Sirve la carpeta auto-contenida (HTML + audios + imágenes) en localhost y abre
el navegador. Es LOCAL: no expone nada a internet (solo alcanza tu máquina).

Uso:
    python3 serve.py --dir ./mi-obra [--port 8000] [--open tablero_audio.html]

Detecta el intérprete de Python según el SO (python3 en Linux/macOS, py en
Windows) y selecciona el navegador por defecto del sistema.
"""

import argparse
import os
import platform
import shutil
import sys
import threading
import time
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


def python_cmd() -> str:
    """Comando de python para lanzar http.server según el SO."""
    if platform.system() == "Windows":
        return "py" if shutil.which("py") else sys.executable
    return sys.executable


def open_browser(url: str, delay: float = 1.0) -> None:
    def _open():
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception as exc:  # pragma: no cover
            print(f"No pude abrir el navegador automáticamente: {exc}")
            print(f"Abre manualmente: {url}")

    threading.Thread(target=_open, daemon=True).start()


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Sirve la carpeta localmente y abre el navegador.")
    ap.add_argument("--dir", default=".",
                    help="carpeta del tablero (default: .)")
    ap.add_argument("--port", type=int, default=8000,
                    help="puerto (default: 8000)")
    ap.add_argument("--open", default="tablero_audio.html",
                    help="archivo a abrir (default: tablero_audio.html)")
    ap.add_argument("--no-browser", action="store_true",
                    help="no abrir navegador, solo publicar el servidor")
    args = ap.parse_args()

    if not os.path.isdir(args.dir):
        print(f"La carpeta '{args.dir}' no existe.")
        return 1

    os.chdir(args.dir)

    handler = partial(SimpleHTTPRequestHandler, directory=".")
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    except OSError as exc:
        print(f"No pude levantar el servidor en el puerto {args.port}: {exc}")
        return 1

    url = f"http://127.0.0.1:{args.port}/{args.open}"
    print(f"Servidor local activo (solo tu máquina): http://127.0.0.1:{args.port}")
    print(f"Tablero: {url}")
    print("Presiona Ctrl+C para detener.")
    print("ADVERTENCIA: esto es local. Publica la carpeta solo si confirmaste "
          "los derechos o licencias de todos sus recursos.")

    if not args.no_browser:
        open_browser(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDeteniendo servidor...")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
