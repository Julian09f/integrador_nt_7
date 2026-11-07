"""Consultas de la HU Q01 sobre la tabla prioridades.

Uso:
    python notebook/consultas/consultar_prioridades.py
    python notebook/consultas/consultar_prioridades.py datos/limpios/prioridades_limpio_q01.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARCHIVO = ROOT / "datos" / "limpios" / "prioridades_limpio_q01.csv"
CARPETA_REPORTES = ROOT / "datos" / "reportes"

# Columnas requeridas por la HU Q01
COLUMNAS = [
    "id",
    "titulo",
    "prioridad",
    "estado",
    "responsable",
    "dias_estimados",
    "fecha_limite",
]


def cargar_datos(ruta: str | Path) -> pd.DataFrame:
    """Lee el CSV y valida que existan las columnas esperadas."""
    ruta = Path(ruta).expanduser().resolve()
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo '{ruta}'.")

    df = pd.read_csv(ruta)
    faltantes = [col for col in COLUMNAS if col not in df.columns]
    if faltantes:
        raise ValueError(
            f"Faltan columnas en el CSV: {faltantes}. "
            "Se espera un archivo con columnas: " + ", ".join(COLUMNAS)
        )

    df["dias_estimados"] = pd.to_numeric(df["dias_estimados"], errors="coerce")
    df["fecha_limite"] = pd.to_datetime(df["fecha_limite"], errors="coerce")
    return df


def resolver_ruta_entrada(argv: list[str]) -> Path:
    """Resuelve la ruta del CSV. Usa la recibida por argumento o un archivo por defecto válido."""
    if len(argv) == 2:
        return Path(argv[1]).expanduser().resolve()

    candidatos = [
        DEFAULT_ARCHIVO,
        ROOT / "datos" / "limpios" / "prioridades_limpio.csv",
        ROOT / "datos" / "crudos" / "prioridades_sucio.csv",
        Path("datos") / "limpios" / "prioridades_limpio_q01.csv",
        Path("datos") / "limpios" / "prioridades_limpio.csv",
        Path("prioridades_limpio_q01.csv"),
        Path("prioridades_limpio.csv"),
    ]
    for ruta in candidatos:
        if ruta.exists():
            return ruta

    return DEFAULT_ARCHIVO


def consulta_1(df: pd.DataFrame) -> pd.DataFrame:
    """Q01-1: cantidad de prioridades por nivel (usa groupby)."""
    return (
        df.groupby("prioridad")
        .size()
        .reset_index(name="total")
        .sort_values(["total", "prioridad"], ascending=[False, True])
    )


def consulta_2(df: pd.DataFrame) -> pd.DataFrame:
    """Q01-2: prioridades Alta que aún no están completadas (filtro)."""
    filtro = (df["prioridad"] == "Alta") & (df["estado"] != "Completada")
    return df.loc[filtro, ["id", "titulo", "estado", "responsable"]]


def consulta_3(df: pd.DataFrame) -> pd.DataFrame:
    """Q01-3: promedio de días estimados por nivel de prioridad (groupby)."""
    return (
        df.groupby("prioridad")["dias_estimados"]
        .mean()
        .round(2)
        .reset_index(name="promedio_dias")
    )


def consulta_4(df: pd.DataFrame) -> pd.DataFrame:
    """Q01-4: los 3 responsables con más prioridades asignadas."""
    con_resp = df.dropna(subset=["responsable"])
    return (
        con_resp.groupby("responsable")
        .size()
        .reset_index(name="total")
        .sort_values(["total", "responsable"], ascending=[False, True])
        .head(3)
    )


def consulta_5(df: pd.DataFrame) -> pd.DataFrame:
    """Q01-5: prioridades no completadas ordenadas por fecha límite."""
    pendientes = df[df["estado"] != "Completada"]
    return pendientes.sort_values("fecha_limite", na_position="last")[
        ["id", "titulo", "prioridad", "fecha_limite"]
    ]


def main() -> int:
    """Ejecuta las cinco consultas, imprime y guarda cada resultado."""
    if len(sys.argv) > 2:
        print("Uso: python notebook/consultas/consultar_prioridades.py [datos/limpios/prioridades_limpio_q01.csv]")
        return 1

    ruta_entrada = resolver_ruta_entrada(sys.argv)

    try:
        df = cargar_datos(ruta_entrada)
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return 1
    except (ValueError, pd.errors.EmptyDataError) as exc:
        print(f"Error al leer el archivo: {exc}")
        return 1

    consultas = [
        ("Consulta 1: cantidad de prioridades por nivel", consulta_1),
        ("Consulta 2: prioridades Alta no completadas", consulta_2),
        ("Consulta 3: promedio de días estimados por nivel", consulta_3),
        ("Consulta 4: top 3 responsables con más prioridades", consulta_4),
        ("Consulta 5: pendientes ordenadas por fecha límite", consulta_5),
    ]

    CARPETA_REPORTES.mkdir(parents=True, exist_ok=True)

    for n, (titulo, funcion) in enumerate(consultas, start=1):
        resultado = funcion(df)
        print(f"\n=== {titulo} ===")
        if len(resultado):
            print(resultado.to_string(index=False))
        else:
            print("(sin resultados)")
        destino = CARPETA_REPORTES / f"prioridades_consulta_{n}.csv"
        resultado.to_csv(destino, index=False)
        print(f"Archivo guardado: {destino}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
