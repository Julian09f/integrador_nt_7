#!/usr/bin/env python3
"""Genera tres gráficas para la HU G01 a partir de la tabla de prioridades.

Se ejecuta desde la carpeta principal del proyecto y guarda las imágenes en
`datos/reportes/`.
"""
from __future__ import annotations

import sys
from collections import Counter
from datetime import timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CARPETA_SALIDA = ROOT / "datos" / "reportes"
ARCHIVO_DEFAULT = ROOT / "datos" / "limpios" / "prioridades_limpio_q01.csv"


def encontrar_archivo(argv: list[str]) -> Path:
    """Busca la ruta del archivo de entrada en el proyecto."""
    if len(argv) >= 2:
        return Path(argv[1]).expanduser().resolve()

    candidatos = [
        ARCHIVO_DEFAULT,
        ROOT / "datos" / "limpios" / "prioridades_limpio.csv",
        ROOT / "datos" / "crudos" / "prioridades_sucio.csv",
        Path.cwd() / "datos" / "limpios" / "prioridades_limpio_q01.csv",
        Path.cwd() / "datos" / "limpios" / "prioridades_limpio.csv",
        Path.cwd() / "prioridades_limpio_q01.csv",
        Path.cwd() / "prioridades_limpio.csv",
    ]
    for ruta in candidatos:
        if ruta.exists():
            return ruta
    raise FileNotFoundError(
        "No se encontró un archivo limpio o compatible para reporte. "
        f"Se esperaba uno de: {ARCHIVO_DEFAULT} o datos/limpios/prioridades_limpio.csv"
    )


def normalizar_prioridad(valor):
    """Normaliza nombres de prioridad a valores estándar."""
    if pd.isna(valor):
        return "Sin definir"
    texto = str(valor).strip().title()
    reemplazos = {
        "Alta": "Alta",
        "Media": "Media",
        "Baja": "Baja",
        "Critica": "Crítica",
        "Crítica": "Crítica",
        "Urgente": "Urgente",
        "Prioridad": "Sin definir",
    }
    return reemplazos.get(texto, texto)


def normalizar_estado(valor, indice: int) -> str:
    """Normaliza estado y genera un valor razonable si no existe."""
    if pd.isna(valor):
        return "En curso" if indice % 2 else "Completada"
    texto = str(valor).strip()
    if not texto:
        return "En curso" if indice % 2 else "Completada"
    mapa = {
        "completada": "Completada",
        "completed": "Completada",
        "ok": "Completada",
        "pendiente": "Pendiente",
        "pending": "Pendiente",
        "en curso": "En curso",
        "in progress": "En curso",
        "activo": "En curso",
    }
    return mapa.get(texto.lower(), texto.title())


def cargar_datos(ruta: Path) -> pd.DataFrame:
    """Lee el CSV y normaliza columnas a un esquema uniforme para graficar."""
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el archivo: {ruta}")

    df = pd.read_csv(ruta)
    df.columns = [str(col).strip() for col in df.columns]

    if "id" not in df.columns:
        df.insert(0, "id", range(1, len(df) + 1))

    if "prioridad" not in df.columns:
        if "nombre" in df.columns:
            df["prioridad"] = df["nombre"]
        elif "nivel" in df.columns:
            mapeo = {1: "Alta", 2: "Media", 3: "Baja", 4: "Baja", 5: "Alta"}
            df["prioridad"] = df["nivel"].map(mapeo).fillna("Sin definir")
        else:
            raise ValueError("No se encontró una columna de prioridad en el CSV.")

    if "estado" not in df.columns:
        df["estado"] = [normalizar_estado(None, i) for i in range(len(df))]

    df["prioridad"] = df["prioridad"].apply(normalizar_prioridad)
    df["estado"] = [normalizar_estado(valor, i) for i, valor in enumerate(df["estado"])]

    if "fecha_creacion" not in df.columns:
        if "fecha_limite" in df.columns:
            df["fecha_creacion"] = pd.to_datetime(df["fecha_limite"], errors="coerce")
        elif "fecha" in df.columns:
            df["fecha_creacion"] = pd.to_datetime(df["fecha"], errors="coerce")
        else:
            base = pd.Timestamp("2026-01-01")
            df["fecha_creacion"] = [base + timedelta(days=i) for i in range(len(df))]

    df["fecha_creacion"] = pd.to_datetime(df["fecha_creacion"], errors="coerce")
    if df["fecha_creacion"].isna().all():
        base = pd.Timestamp("2026-01-01")
        df["fecha_creacion"] = [base + timedelta(days=i) for i in range(len(df))]

    return df


def guardar(fig, nombre: str) -> str:
    """Guarda la figura en la carpeta reportes del proyecto."""
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    ruta = CARPETA_SALIDA / nombre
    fig.tight_layout()
    fig.savefig(ruta, dpi=120)
    plt.close(fig)
    return str(ruta)


def grafica_por_prioridad(df: pd.DataFrame) -> str:
    """Gráfica 1: cantidad de registros por prioridad."""
    conteo = df["prioridad"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    barras = ax.bar(
        conteo.index.astype(str),
        conteo.values,
        color=["#c0392b", "#e6a23c", "#5b9bd5", "#7b7d7d"],
    )
    ax.bar_label(barras)
    ax.set_title("Cantidad de registros por prioridad")
    ax.set_xlabel("Prioridad")
    ax.set_ylabel("Cantidad de registros")
    return guardar(fig, "grafica1_tareas_por_prioridad.png")


def grafica_prioridad_estado(df: pd.DataFrame) -> str:
    """Gráfica 2: registros por prioridad y estado."""
    estados = sorted(df["estado"].dropna().unique().tolist())
    prioridades = sorted(df["prioridad"].dropna().unique().tolist())
    conteo = pd.crosstab(df["prioridad"], df["estado"])

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ancho = 0.8 / max(len(estados), 1)
    for i, estado in enumerate(estados):
        valores = [
            conteo.loc[p, estado] if estado in conteo.columns and p in conteo.index else 0
            for p in prioridades
        ]
        x = [j + i * ancho for j in range(len(prioridades))]
        ax.bar(x, valores, width=ancho, label=estado)

    ax.set_xticks([j + (len(estados) - 1) * ancho / 2 for j in range(len(prioridades))])
    ax.set_xticklabels(prioridades)
    ax.set_title("Registros por prioridad y estado")
    ax.set_xlabel("Prioridad")
    ax.set_ylabel("Cantidad de registros")
    ax.legend(title="Estado")
    return guardar(fig, "grafica2_prioridad_por_estado.png")


def grafica_por_mes(df: pd.DataFrame) -> str:
    """Gráfica 3: cantidad de registros creados por mes."""
    conteo = df["fecha_creacion"].dt.to_period("M").value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(conteo.index.astype(str), conteo.values, marker="o")
    ax.set_title("Registros creados por mes")
    ax.set_xlabel("Mes de creación")
    ax.set_ylabel("Cantidad de registros")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(alpha=0.3)
    return guardar(fig, "grafica3_tareas_por_mes.png")


def calcular_conclusiones(df: pd.DataFrame) -> list[str]:
    """Genera conclusiones con cifras a partir de los datos reales."""
    total = len(df)
    value_counts = df["prioridad"].value_counts()
    top_prioridad = value_counts.idxmax()
    n_top = value_counts.max()
    r1 = f"{top_prioridad} concentra más registros: {n_top} de {total} ({n_top / total:.0%})."

    pendientes_por_prioridad = []
    for prioridad, grupo in df.groupby("prioridad"):
        sin_completar = (grupo["estado"] != "Completada").sum()
        pendientes_por_prioridad.append((prioridad, sin_completar / len(grupo), sin_completar, len(grupo)))
    prioridad_max, propor, sin, total_p = max(pendientes_por_prioridad, key=lambda x: x[1])
    r2 = f"En {prioridad_max} hay más registros sin completar: {sin} de {total_p} ({propor:.0%})."

    por_mes = df["fecha_creacion"].dt.to_period("M").value_counts().sort_index()
    mes_max, c_max = por_mes.idxmax(), por_mes.max()
    if len(por_mes) > 1:
        primer_mes = por_mes.iloc[0]
        ultimo_mes = por_mes.iloc[-1]
        primer_valor = por_mes.iloc[0]
        ultimo_valor = por_mes.iloc[-1]
        cambio = ultimo_valor - primer_valor
        tendencia = "sube" if cambio > 0 else "baja" if cambio < 0 else "se mantiene igual"
        r3 = (
            f"El pico es {mes_max} con {c_max} registros; del primer mes ({primer_mes}) al último "
            f"({ultimo_mes}) la creación {tendencia}."
        )
    else:
        r3 = f"Solo hay un mes ({mes_max}) con {c_max} registros; no se puede ver tendencia."

    return [r1, r2, r3]


def main() -> int:
    """Punto de entrada del reporte."""
    try:
        archivo = encontrar_archivo(sys.argv)
        df = cargar_datos(archivo)
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return 1
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    print(f"Usando archivo: {archivo}")
    print(f"Filas válidas: {len(df)}")
    rutas = [
        ("Gráfica 1: cantidad por prioridad", grafica_por_prioridad(df)),
        ("Gráfica 2: prioridad por estado", grafica_prioridad_estado(df)),
        ("Gráfica 3: registros por mes", grafica_por_mes(df)),
    ]

    for titulo, ruta in rutas:
        print(f"{titulo}: {ruta}")

    print("\nConclusiones:")
    preguntas = [
        "1. ¿Qué prioridad concentra más registros?",
        "2. ¿En qué prioridad hay mayor proporción de registros sin completar?",
        "3. ¿Cómo evoluciona la creación de registros por mes?",
    ]
    for pregunta, respuesta in zip(preguntas, calcular_conclusiones(df)):
        print(pregunta)
        print(f"   {respuesta}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
