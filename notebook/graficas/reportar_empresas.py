"""Tres graficas y conclusiones de `empresas` con matplotlib.

Lee el archivo LIMPIO, reutiliza las consultas de la etapa anterior, guarda
las graficas en datos/reportes/ y un resumen JSON (el front lo muestra).

Uso:
    python notebook/graficas/reportar_empresas.py
"""

import json
import os
import sys
from importlib import import_module

import matplotlib

matplotlib.use("Agg")  # sin ventana: el script no se queda esperando
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "consultas"))
consultas = import_module("consultar_empresas")

sys.stdout.reconfigure(encoding="utf-8")  # tildes y ñ en la consola de Windows

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CARPETA_REPORTES = os.path.join(RAIZ, "datos", "reportes")

AZUL, NARANJA, GRIS = "#2f5bea", "#e8743b", "#8a94a6"


def grafica_1(por_sector):
    ax = por_sector.plot(kind="bar", color=AZUL, figsize=(8, 5))
    ax.set_title("Cantidad de empresas por sector")
    ax.set_xlabel("Sector")
    ax.set_ylabel("Numero de empresas")
    for c in ax.containers:
        ax.bar_label(c, padding=2)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    return _guardar(1)


def grafica_2(df):
    conteo = df["activa"].value_counts()
    etiquetas = ["Activas" if k else "Inactivas" for k in conteo.index]
    ax = conteo.plot(kind="pie", autopct="%1.1f%%", labels=etiquetas,
                     colors=[AZUL if k else NARANJA for k in conteo.index], figsize=(6, 6))
    ax.set_title("Empresas activas vs inactivas")
    ax.set_xlabel("Estado de la empresa")   # la torta no tiene ejes: se rotulan igual
    ax.set_ylabel("Proporcion")
    plt.tight_layout()
    return _guardar(2)


def grafica_3(tabla):
    tabla = tabla.rename(columns={True: "Activas", False: "Inactivas"})
    ax = tabla.plot(kind="bar", stacked=True, color=[NARANJA, AZUL], figsize=(8, 5))
    ax.set_title("Empresas activas e inactivas por sector")
    ax.set_xlabel("Sector")
    ax.set_ylabel("Numero de empresas")
    ax.legend(title="Estado")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    return _guardar(3)


def _guardar(n):
    os.makedirs(CARPETA_REPORTES, exist_ok=True)
    ruta = os.path.join(CARPETA_REPORTES, f"empresas_grafica_{n}.png")
    plt.savefig(ruta, dpi=120)
    plt.close()
    return ruta


def conclusiones(df, por_sector):
    top, n_top = por_sector.index[0], int(por_sector.iloc[0])
    bajo, n_bajo = por_sector.index[-1], int(por_sector.iloc[-1])
    pct_inactivas = round((~df["activa"]).mean() * 100, 1)
    n_invalidos = int((~df["correo_valido"]).sum())
    n_sin_contacto = int((df["contacto"] == "Sin contacto").sum())
    return [
        f"El sector con mas empresas registradas es {top} ({n_top} de {len(df)}); "
        f"el de menos es {bajo} ({n_bajo}).",
        f"{pct_inactivas}% de las empresas esta inactivo: son organizaciones que no "
        "pueden publicar retos, asi que la plataforma debe incentivar su reactivacion.",
        f"Aparecieron {n_invalidos} correos invalidos (sin '@'): hay que validar el "
        "correo en el registro para no perder el contacto con la empresa.",
        f"{n_sin_contacto} empresas no tienen persona de contacto: conviene hacerlo "
        "obligatorio en el formulario.",
    ]


if __name__ == "__main__":
    df = consultas.cargar()
    por_sector = df.groupby("sector")["id"].count().sort_values(ascending=False)
    tabla = df.groupby(["sector", "activa"])["id"].count().unstack(fill_value=0)

    rutas = [grafica_1(por_sector), grafica_2(df), grafica_3(tabla)]
    for r in rutas:
        print("Grafica guardada:", r)

    texto = conclusiones(df, por_sector)
    print("\n===== CONCLUSIONES =====")
    for i, linea in enumerate(texto, 1):
        print(f"{i}. {linea}")

    resumen = {
        "total": int(len(df)),
        "activas": int(df["activa"].sum()),
        "inactivas": int((~df["activa"]).sum()),
        "correos_invalidos": int((~df["correo_valido"]).sum()),
        "por_sector": {k: int(v) for k, v in por_sector.items()},
        "conclusiones": texto,
        "graficas": [
            {"archivo": f"empresas_grafica_{i}.png", "titulo": t}
            for i, t in enumerate(
                ["Empresas por sector", "Activas vs inactivas", "Activas e inactivas por sector"], 1)
        ],
    }
    ruta_json = os.path.join(CARPETA_REPORTES, "empresas_resumen.json")
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)
    print("\nResumen para el front:", ruta_json)
