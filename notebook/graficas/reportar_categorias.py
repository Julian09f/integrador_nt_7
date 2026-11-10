"""Tres graficas y conclusiones de `categorias` con matplotlib.

Lee el archivo LIMPIO, reutiliza las consultas, guarda las graficas en
datos/reportes/ y un resumen JSON que muestra el front.

Uso:
    python notebook/graficas/reportar_categorias.py
"""

import json
import os
import sys
from importlib import import_module

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "consultas"))
consultas = import_module("consultar_categorias")

sys.stdout.reconfigure(encoding="utf-8")  # tildes y ñ en la consola de Windows

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CARPETA_REPORTES = os.path.join(RAIZ, "datos", "reportes")
RUTA_CRUDO = os.path.join(RAIZ, "datos", "crudos", "categorias_sucio.csv")
AZUL, VERDE = "#2f5bea", "#1f9d73"


def _guardar(n):
    os.makedirs(CARPETA_REPORTES, exist_ok=True)
    ruta = os.path.join(CARPETA_REPORTES, f"categorias_grafica_{n}.png")
    plt.savefig(ruta, dpi=120)
    plt.close()
    return ruta


def grafica_1(conteo):
    ax = conteo.sort_values().plot(kind="barh", color=AZUL, figsize=(8, 5))
    ax.set_title("Cuantas veces aparece cada categoria")
    ax.set_xlabel("Numero de filas")
    ax.set_ylabel("Categoria")
    for c in ax.containers:
        ax.bar_label(c, padding=2)
    plt.tight_layout()
    return _guardar(1)


def grafica_2(por_area):
    ax = por_area.plot(kind="pie", autopct="%1.1f%%", figsize=(8, 6))
    ax.set_title("Reparto de categorias por area responsable")
    ax.set_xlabel("Area responsable")
    ax.set_ylabel("Proporcion", labelpad=40)
    plt.tight_layout()
    return _guardar(2)


def grafica_3(largos):
    ax = largos.plot(kind="bar", color=VERDE, figsize=(8, 5))
    ax.set_title("Largo promedio de la descripcion por categoria")
    ax.set_xlabel("Categoria")
    ax.set_ylabel("Caracteres (promedio)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    return _guardar(3)


def conclusiones(df):
    crudo = pd.read_csv(RUTA_CRUDO)
    filas_crudo, filas_limpio = len(crudo), len(df)
    duplicados = int(crudo.duplicated().sum())
    variantes = int(crudo["nombre"].nunique())
    reales = int(df["nombre"].nunique())
    sin_desc = int((df["descripcion"] == "Sin descripcion").sum())
    return [
        f"Se eliminaron {filas_crudo - filas_limpio} filas ({filas_crudo} -> {filas_limpio}): "
        f"{duplicados} duplicados exactos. Ademas se unificaron las variantes de escritura: "
        f"el archivo sucio tenia {variantes} nombres distintos y quedaron {reales}.",
        f"Quedaron {reales} categorias REALES (deberian ser 10).",
        "El back debe declarar `nombre` como UNICO (UNIQUE en la base de datos y en el "
        "esquema): asi 'Logistica', 'LOGISTICA', ' logistica ' o 'logística' no se pueden "
        "guardar como categorias distintas y el catalogo no vuelve a llenarse de variantes.",
        f"{sin_desc} categorias no tienen descripcion: conviene hacerla obligatoria.",
    ]


if __name__ == "__main__":
    df = consultas.cargar()
    conteo = df["nombre"].value_counts()
    por_area = df.groupby("area_responsable")["id"].count().sort_values(ascending=False)
    largos = df.groupby("nombre")["largo_desc"].mean().round(1).sort_values(ascending=False)

    for r in (grafica_1(conteo), grafica_2(por_area), grafica_3(largos)):
        print("Grafica guardada:", r)

    texto = conclusiones(df)
    print("\n===== CONCLUSIONES =====")
    for i, t in enumerate(texto, 1):
        print(f"{i}. {t}")

    resumen = {
        "total": int(len(df)),
        "categorias_reales": int(df["nombre"].nunique()),
        "sin_descripcion": int((df["descripcion"] == "Sin descripcion").sum()),
        "areas": int(df["area_responsable"].nunique()),
        "conclusiones": texto,
        "graficas": [
            {"archivo": "categorias_grafica_1.png", "titulo": "Apariciones por categoría"},
            {"archivo": "categorias_grafica_2.png", "titulo": "Categorías por área responsable"},
            {"archivo": "categorias_grafica_3.png", "titulo": "Largo promedio de la descripción"},
        ],
    }
    ruta = os.path.join(CARPETA_REPORTES, "categorias_resumen.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)
    print("\nResumen para el front:", ruta)
