"""Limpia la tabla de prioridades y guarda la versión limpia.

Uso:
    python notebook/limpieza/limpiar_prioridades.py
    python notebook/limpieza/limpiar_prioridades.py datos/crudos/prioridades_sucio.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_ARCHIVO = "prioridades_sucio.csv"
CARPETA_CRUDOS = ROOT / "datos" / "crudos"
CARPETA_LIMPIOS = ROOT / "datos" / "limpios"


def normalizar_nombre(valor):
    """Quita espacios y unifica el nombre de la prioridad en formato estable."""
    if pd.isna(valor):
        return None
    texto = str(valor).strip()
    if not texto:
        return None
    return texto.title()


def normalizar_nivel(valor):
    """Convierte variantes de nivel a entero de 1 a 5 y devuelve None si es inválido."""
    if pd.isna(valor):
        return None

    texto = str(valor).strip().lower()
    mapa = {
        "1": 1,
        "uno": 1,
        "2": 2,
        "dos": 2,
        "3": 3,
        "tres": 3,
        "4": 4,
        "cuatro": 4,
        "5": 5,
        "cinco": 5,
    }

    if texto in mapa:
        return int(mapa[texto])

    try:
        numero = int(float(texto))
    except ValueError:
        return None
    return numero if numero in {1, 2, 3, 4, 5} else None


def normalizar_dias(valor):
    """Normaliza la columna de días y elimina valores absurdos como 999."""
    if pd.isna(valor):
        return None

    try:
        numero = int(float(str(valor).strip()))
    except ValueError:
        return None

    return numero if numero > 0 else None


def diagnostico(df: pd.DataFrame, titulo: str) -> None:
    """Imprime un resumen del DataFrame antes o después de la limpieza."""
    print(f"\n=== {titulo} ===")
    print(f"shape: {df.shape}")
    print("nulos por columna:")
    print(df.isna().sum().to_string())
    print("duplicados completos:", int(df.duplicated().sum()))
    if not df.empty:
        print(df.head().to_string(index=False))


def resolver_ruta_entrada(ruta_arg: str | None) -> Path:
    """Resuelve la ruta del CSV sucio, tomando la recibida o un valor por defecto válido."""
    if ruta_arg:
        return Path(ruta_arg).expanduser().resolve()

    candidatos = [
        ROOT / "datos" / "crudos" / DEFAULT_ARCHIVO,
        ROOT / DEFAULT_ARCHIVO,
        Path("datos") / "crudos" / DEFAULT_ARCHIVO,
        Path(DEFAULT_ARCHIVO),
    ]
    for ruta in candidatos:
        if ruta.exists():
            return ruta
    return CARPETA_CRUDOS / DEFAULT_ARCHIVO


def convertir_a_formato_q01(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte el dataset limpio de la fase de preparación a un formato compatible con Q01."""
    if {"id", "nombre", "nivel", "dias_max_respuesta"}.difference(df.columns):
        return df.copy()

    q01 = df.copy()
    q01 = q01.rename(columns={"nombre": "titulo", "nivel": "prioridad", "dias_max_respuesta": "dias_estimados"})

    mapa_prioridad = {1: "Crítica", 2: "Alta", 3: "Media", 4: "Baja", 5: "Urgente"}
    q01["prioridad"] = pd.to_numeric(q01["prioridad"], errors="coerce")
    q01["prioridad"] = q01["prioridad"].map(mapa_prioridad).fillna("Sin definir")

    q01["estado"] = "Pendiente"
    q01["responsable"] = "Sin asignar"
    q01["dias_estimados"] = pd.to_numeric(q01["dias_estimados"], errors="coerce").fillna(1)
    q01["fecha_limite"] = pd.Timestamp.today().normalize() + pd.to_timedelta(q01["dias_estimados"], unit="D")

    return q01[["id", "titulo", "prioridad", "estado", "responsable", "dias_estimados", "fecha_limite"]]


def main() -> int:
    """Lee el CSV sucio, limpia los datos y guarda un CSV limpio."""
    parser = argparse.ArgumentParser(description="Limpia la tabla de prioridades.")
    parser.add_argument("archivo", nargs="?", default=None, help="Ruta al CSV sucio. Si no se da, busca en datos/crudos o en la raíz")
    args = parser.parse_args()

    ruta = resolver_ruta_entrada(args.archivo)
    if not ruta.exists():
        print(f"ERROR: no existe el archivo {ruta}")
        print(f"Prueba con: python notebook/limpieza/limpiar_prioridades.py datos/crudos/{DEFAULT_ARCHIVO}")
        return 1

    df = pd.read_csv(ruta)
    diagnostico(df, "ANTES")

    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]

    columnas = ["id", "nombre", "nivel", "dias_max_respuesta"]
    for col in columnas:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    if "nombre" in df.columns:
        df["nombre"] = df["nombre"].map(normalizar_nombre)
    if "nivel" in df.columns:
        df["nivel"] = df["nivel"].map(normalizar_nivel)
    if "dias_max_respuesta" in df.columns:
        df["dias_max_respuesta"] = df["dias_max_respuesta"].map(normalizar_dias)

    df = df.dropna(subset=[col for col in columnas if col in df.columns])
    df = df.drop_duplicates(subset=["id"], keep="first").reset_index(drop=True)

    diagnostico(df, "DESPUÉS")

    CARPETA_LIMPIOS.mkdir(parents=True, exist_ok=True)
    salida = CARPETA_LIMPIOS / "prioridades_limpio.csv"
    df.to_csv(salida, index=False, encoding="utf-8")
    print(f"\nArchivo limpio guardado en: {salida}")

    q01 = convertir_a_formato_q01(df)
    salida_q01 = CARPETA_LIMPIOS / "prioridades_limpio_q01.csv"
    q01.to_csv(salida_q01, index=False, encoding="utf-8")
    print(f"Archivo compatible con consultas guardado en: {salida_q01}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
