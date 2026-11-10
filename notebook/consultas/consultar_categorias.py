"""Cinco consultas sobre `categorias` (3 con groupby).

Lee el archivo LIMPIO y guarda cada respuesta en
datos/reportes/categorias_consulta_N.csv. Cada consulta esta en su propia funcion.

Uso:
    python notebook/consultas/consultar_categorias.py
"""

import os
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")  # tildes y ñ en la consola de Windows

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CARPETA_LIMPIO = os.path.join(RAIZ, "datos", "limpios")
RUTA_LIMPIO = os.path.join(CARPETA_LIMPIO, "categorias_limpio.csv")
CARPETA_SALIDA = os.path.join(RAIZ, "datos", "reportes")


def cargar():
    return pd.read_csv(RUTA_LIMPIO)


def _guardar(resultado, n, con_indice):
    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    ruta = os.path.join(CARPETA_SALIDA, f"categorias_consulta_{n}.csv")
    resultado.to_csv(ruta, index=con_indice, encoding="utf-8")


def consulta_1(df):
    print("\n--- Consulta 1: ¿Cuantas veces aparece cada categoria? (detecta variantes) ---")
    conteo = df["nombre"].value_counts()
    print(conteo)
    _guardar(conteo, 1, True)
    return conteo


def consulta_2(df):
    print("\n--- Consulta 2: Categorias sin descripcion ---")
    sin_desc = df[df["descripcion"] == "Sin descripcion"]
    print(sin_desc.head(10))
    print(f"Total sin descripcion: {len(sin_desc)}")
    _guardar(sin_desc, 2, False)
    return sin_desc


def consulta_3(df):
    print("\n--- Consulta 3 (GROUPBY): largo promedio de la descripcion por categoria ---")
    largos = df.groupby("nombre")["largo_desc"].mean().round(1).sort_values(ascending=False)
    print(largos)
    _guardar(largos, 3, True)
    return largos


def consulta_4(df):
    print("\n--- Consulta 4 (GROUPBY): ¿cuantas categorias maneja cada area? ---")
    por_area = df.groupby("area_responsable")["id"].count().sort_values(ascending=False)
    print(por_area)
    _guardar(por_area, 4, True)
    return por_area


def consulta_5(df):
    print("\n--- Consulta 5 (GROUPBY doble): categorias por area (tabla cruzada) ---")
    tabla = df.groupby(["area_responsable", "nombre"])["id"].count().unstack(fill_value=0)
    print(tabla)
    _guardar(tabla, 5, True)
    return tabla


def ejecutar_consultas(df):
    return {
        "conteo": consulta_1(df),
        "sin_desc": consulta_2(df),
        "largos": consulta_3(df),
        "por_area": consulta_4(df),
        "tabla": consulta_5(df),
    }


if __name__ == "__main__":
    ejecutar_consultas(cargar())
