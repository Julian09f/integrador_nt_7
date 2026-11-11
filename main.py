#!/usr/bin/env python3
"""
main.py - Orquestador visual del pipeline del proyecto integrador.

Ejecuta, uno a uno y en este orden, los scripts .py de cada subcarpeta de notebook/:
    1. simulaciones -> 2. exportaciones -> 3. limpieza -> 4. consultas -> 5. graficas
y muestra el resultado de cada archivo (salida, avisos, archivos generados, tablas
y gráficas) en una interfaz web local, dinámica e interactiva.

Uso (desde la raíz del proyecto, con el .venv activado):
    python main.py            # abre la interfaz en el navegador (http://127.0.0.1:8765)
    python main.py --cli      # ejecuta todo en la terminal, sin interfaz
    python main.py --port 9000 --no-browser

Seguridad:
    - Solo escucha en 127.0.0.1 (no expuesto a la red) y valida la cabecera Host (anti DNS rebinding).
    - Solo ejecuta scripts de una lista blanca descubierta al iniciar (nunca rutas enviadas por el cliente).
    - Las peticiones POST exigen un token aleatorio por sesión (anti CSRF).
    - Solo sirve archivos dentro de datos/ (bloquea path traversal) y con extensiones permitidas.
Dependencias: solo biblioteca estándar (los scripts usan las de requirements.txt).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import mimetypes
import os
import secrets
import subprocess
import sys
import threading
import time
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

RAIZ = Path(__file__).resolve().parent
CARPETA_NOTEBOOK = RAIZ / "notebook"
CARPETA_DATOS = RAIZ / "datos"
ARCHIVO_INTERFAZ = RAIZ / "interfaz" / "index.html"

# Orden obligatorio de las fases (subcarpeta, título visible, descripción)
FASES = (
    ("simulaciones", "Simulaciones", "Genera datos sintéticos (sucios a propósito) con Faker."),
    ("exportaciones", "Exportaciones", "Guarda los datos crudos en CSV, JSON y Excel."),
    ("limpieza", "Limpieza", "Corrige, normaliza y deduplica los datos crudos."),
    ("consultas", "Consultas", "Responde las preguntas de negocio con pandas (HU Q01)."),
    ("graficas", "Gráficas", "Genera gráficas y conclusiones con matplotlib (HU G01)."),
)
TIEMPO_MAXIMO_S = 300  # límite por script
EXTENSIONES_SERVIBLES = {".png", ".jpg", ".jpeg", ".svg", ".csv", ".json", ".xlsx"}
MAX_FILAS_PREVIEW = 100
MAX_BYTES_SALIDA = 2 * 1024 * 1024  # recorta salidas gigantes para no saturar el navegador


# ----------------------------------------------------------------------------- descubrimiento
def descubrir_scripts() -> list[dict]:
    """Lista blanca de scripts: cada .py de cada fase, en orden de fase y alfabético."""
    scripts = []
    for numero, (carpeta, titulo, _desc) in enumerate(FASES, start=1):
        ruta_fase = CARPETA_NOTEBOOK / carpeta
        if not ruta_fase.is_dir():
            continue
        for ruta in sorted(ruta_fase.glob("*.py")):
            if ruta.name.startswith("__"):
                continue
            entidad = ruta.stem.split("_", 1)[-1]  # simular_retos -> retos
            scripts.append({
                "id": len(scripts),
                "fase": carpeta,
                "fase_numero": numero,
                "fase_titulo": titulo,
                "archivo": ruta.name,
                "ruta_relativa": ruta.relative_to(RAIZ).as_posix(),
                "entidad": entidad,
                "_ruta": ruta,
            })
    return scripts


def publico(script: dict) -> dict:
    """Copia del script sin campos internos (la ruta absoluta no se expone al navegador)."""
    return {k: v for k, v in script.items() if not k.startswith("_")}


# ----------------------------------------------------------------------------- ejecución
def instantanea_datos() -> dict[str, int]:
    """Mapa ruta_relativa -> mtime de todo lo que hay en datos/ (para detectar archivos generados)."""
    if not CARPETA_DATOS.is_dir():
        return {}
    return {
        p.relative_to(RAIZ).as_posix(): p.stat().st_mtime_ns
        for p in CARPETA_DATOS.rglob("*") if p.is_file()
    }


def recortar(texto: str) -> str:
    if len(texto) > MAX_BYTES_SALIDA:
        return texto[:MAX_BYTES_SALIDA] + "\n\n... [salida recortada por tamaño] ..."
    return texto


def ejecutar_script(script: dict) -> dict:
    """Ejecuta el script en un proceso aislado y devuelve salida, avisos, código y archivos generados."""
    antes = instantanea_datos()
    entorno = os.environ.copy()
    entorno.update({
        "PYTHONIOENCODING": "utf-8",   # tildes y ñ correctas en Windows
        "PYTHONUTF8": "1",
        "MPLBACKEND": "Agg",           # matplotlib sin ventanas: nunca bloquea el pipeline
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    inicio = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, str(script["_ruta"])],
            cwd=str(script["_ruta"].parent),
            env=entorno,
            capture_output=True,
            timeout=TIEMPO_MAXIMO_S,
            check=False,
        )
        codigo = proc.returncode
        salida = proc.stdout.decode("utf-8", errors="replace")
        avisos = proc.stderr.decode("utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        codigo, salida, avisos = -1, "", f"ERROR: el script superó {TIEMPO_MAXIMO_S} s y fue detenido."
    duracion = time.perf_counter() - inicio

    despues = instantanea_datos()
    generados = sorted(r for r, m in despues.items() if antes.get(r) != m)
    return {
        **publico(script),
        "ok": codigo == 0,
        "codigo": codigo,
        "duracion_s": round(duracion, 2),
        "salida": recortar(salida),
        "avisos": recortar(avisos),
        "archivos": [
            {"ruta": r, "tipo": Path(r).suffix.lower().lstrip("."),
             "bytes": (RAIZ / r).stat().st_size}
            for r in generados
        ],
    }


# ----------------------------------------------------------------------------- utilidades de archivos
def ruta_segura(relativa: str) -> Path | None:
    """Resuelve una ruta pedida por el navegador solo si queda dentro de datos/ y con extensión permitida."""
    try:
        ruta = (RAIZ / relativa).resolve()
        ruta.relative_to(CARPETA_DATOS.resolve())
    except (ValueError, OSError):
        return None
    if not ruta.is_file() or ruta.suffix.lower() not in EXTENSIONES_SERVIBLES:
        return None
    return ruta


def previsualizar_csv(ruta: Path) -> dict:
    """Lee las primeras filas de un CSV detectando el separador (; o ,)."""
    texto = ruta.read_text(encoding="utf-8-sig", errors="replace")
    try:
        dialecto = csv.Sniffer().sniff(texto[:4096], delimiters=";,\t")
    except csv.Error:
        dialecto = csv.excel
    lector = csv.reader(io.StringIO(texto), dialecto)
    filas = list(lector)
    if not filas:
        return {"columnas": [], "filas": [], "total": 0}
    return {"columnas": filas[0], "filas": filas[1:MAX_FILAS_PREVIEW + 1], "total": len(filas) - 1}


# ----------------------------------------------------------------------------- servidor web
class Manejador(BaseHTTPRequestHandler):
    scripts: list[dict] = []
    token: str = ""
    hosts_validos: set[str] = set()
    candado = threading.Lock()  # un solo script a la vez (los pasos dependen entre sí)

    def log_message(self, formato, *args):  # silencia el log por petición
        pass

    # -- respuestas
    def _enviar(self, estado: int, cuerpo: bytes, tipo: str) -> None:
        self.send_response(estado)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _json(self, datos, estado: int = 200) -> None:
        self._enviar(estado, json.dumps(datos, ensure_ascii=False).encode("utf-8"),
                     "application/json; charset=utf-8")

    def _host_valido(self) -> bool:
        if self.headers.get("Host", "") not in self.hosts_validos:
            self._json({"error": "Host no permitido"}, HTTPStatus.FORBIDDEN)
            return False
        return True

    # -- GET
    def do_GET(self):
        if not self._host_valido():
            return
        url = urlparse(self.path)
        consulta = parse_qs(url.query)

        if url.path in ("/", "/index.html"):
            html = ARCHIVO_INTERFAZ.read_text(encoding="utf-8").replace("__TOKEN__", self.token)
            self._enviar(200, html.encode("utf-8"), "text/html; charset=utf-8")
        elif url.path == "/api/plan":
            self._json({
                "fases": [{"carpeta": c, "titulo": t, "descripcion": d, "numero": i}
                          for i, (c, t, d) in enumerate(FASES, start=1)],
                "scripts": [publico(s) for s in self.scripts],
                "python": sys.version.split()[0],
            })
        elif url.path == "/api/preview":
            ruta = ruta_segura(consulta.get("ruta", [""])[0])
            if ruta is None or ruta.suffix.lower() != ".csv":
                self._json({"error": "Archivo no permitido"}, HTTPStatus.NOT_FOUND)
            else:
                self._json(previsualizar_csv(ruta))
        elif url.path == "/archivo":
            ruta = ruta_segura(consulta.get("ruta", [""])[0])
            if ruta is None:
                self._json({"error": "Archivo no permitido"}, HTTPStatus.NOT_FOUND)
            else:
                tipo = mimetypes.guess_type(ruta.name)[0] or "application/octet-stream"
                self._enviar(200, ruta.read_bytes(), tipo)
        else:
            self._json({"error": "No encontrado"}, HTTPStatus.NOT_FOUND)

    # -- POST
    def do_POST(self):
        if not self._host_valido():
            return
        if not secrets.compare_digest(self.headers.get("X-Token", ""), self.token):
            self._json({"error": "Token inválido"}, HTTPStatus.FORBIDDEN)
            return
        url = urlparse(self.path)
        if url.path != "/api/ejecutar":
            self._json({"error": "No encontrado"}, HTTPStatus.NOT_FOUND)
            return
        try:
            indice = int(parse_qs(url.query).get("id", ["-1"])[0])
            script = self.scripts[indice] if indice >= 0 else None
        except (ValueError, IndexError):
            script = None
        if script is None:
            self._json({"error": "Script desconocido"}, HTTPStatus.BAD_REQUEST)
            return
        if not self.candado.acquire(blocking=False):
            self._json({"error": "Ya hay un script en ejecución"}, HTTPStatus.CONFLICT)
            return
        try:
            self._json(ejecutar_script(script))
        finally:
            self.candado.release()


def iniciar_interfaz(scripts: list[dict], puerto: int, abrir: bool) -> None:
    Manejador.scripts = scripts
    Manejador.token = secrets.token_urlsafe(32)
    Manejador.hosts_validos = {f"127.0.0.1:{puerto}", f"localhost:{puerto}"}
    servidor = ThreadingHTTPServer(("127.0.0.1", puerto), Manejador)
    url = f"http://127.0.0.1:{puerto}/"
    print(f"\n  Pipeline Integrador NT7 -> {url}")
    print(f"  {len(scripts)} scripts en {len(FASES)} fases. Ctrl+C para salir.\n")
    if abrir:
        threading.Timer(0.8, webbrowser.open, args=(url,)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor detenido.")
    finally:
        servidor.server_close()


# ----------------------------------------------------------------------------- modo terminal
def modo_cli(scripts: list[dict], detener_en_error: bool) -> int:
    verde, rojo, cian, amarillo, gris, fin = "\033[92m", "\033[91m", "\033[96m", "\033[93m", "\033[90m", "\033[0m"
    if os.name == "nt":
        os.system("")  # activa colores ANSI en la consola de Windows
    fallos = 0
    fase_actual = None
    for s in scripts:
        if s["fase"] != fase_actual:
            fase_actual = s["fase"]
            print(f"\n{cian}{'=' * 70}\n  FASE {s['fase_numero']}: {s['fase_titulo'].upper()}\n{'=' * 70}{fin}")
        print(f"{amarillo}> {s['ruta_relativa']}{fin}")
        r = ejecutar_script(s)
        if r["salida"].strip():
            print(r["salida"].rstrip())
        if r["avisos"].strip():
            print(f"{amarillo}{r['avisos'].rstrip()}{fin}")
        for a in r["archivos"]:
            print(f"{gris}  + {a['ruta']}{fin}")
        estado = f"{verde}OK{fin}" if r["ok"] else f"{rojo}ERROR (código {r['codigo']}){fin}"
        print(f"  [{estado}] {r['duracion_s']} s\n")
        if not r["ok"]:
            fallos += 1
            if detener_en_error:
                break
    color = verde if fallos == 0 else rojo
    print(f"{color}Resumen: {len(scripts)} scripts, {fallos} con error.{fin}")
    return 1 if fallos else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Ejecuta el pipeline de notebook/ con interfaz visual.")
    parser.add_argument("--cli", action="store_true", help="ejecutar en la terminal, sin interfaz web")
    parser.add_argument("--port", type=int, default=8765, help="puerto local (por defecto 8765)")
    parser.add_argument("--no-browser", action="store_true", help="no abrir el navegador automáticamente")
    parser.add_argument("--detener-en-error", action="store_true", help="(modo --cli) parar en el primer error")
    args = parser.parse_args()

    scripts = descubrir_scripts()
    if not scripts:
        print("No se encontraron scripts en notebook/.", file=sys.stderr)
        return 1
    if args.cli:
        return modo_cli(scripts, args.detener_en_error)
    if not ARCHIVO_INTERFAZ.is_file():
        print(f"Falta la interfaz: {ARCHIVO_INTERFAZ}", file=sys.stderr)
        return 1
    iniciar_interfaz(scripts, args.port, not args.no_browser)
    return 0


if __name__ == "__main__":
    sys.exit(main())
