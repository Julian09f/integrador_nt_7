"""Cinco consultas sobre `empresas` (2 con groupby).

Lee el archivo LIMPIO y guarda cada respuesta en
datos/reportes/empresas_consulta_N.csv. Cada consulta esta en su propia funcion.

Uso:
    python notebook/consultas/consultar_empresas.py
"""

import os
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")  # tildes y ñ en la consola de Windows

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUTA_LIMPIO = os.path.join(RAIZ, "datos", "limpios", "empresas_limpio.csv")
CARPETA_SALIDA = os.path.join(RAIZ, "datos", "reportes")


def cargar():
    """Lee el CSV limpio; `activa` vuelve a ser booleano."""
    df = pd.read_csv(RUTA_LIMPIO, dtype={"nit": str, "telefono": str})
    df["activa"] = df["activa"].astype(bool)
    return df


def _guardar(resultado, n):
    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    ruta = os.path.join(CARPETA_SALIDA, f"empresas_consulta_{n}.csv")
    resultado.to_csv(ruta, index=True if isinstance(resultado, pd.Series) or resultado.index.name else False,
                     encoding="utf-8")


def consulta_1(df):
    print("\n--- Consulta 1: ¿Que empresas estan activas? ---")
    activas = df[df["activa"] == True]  # noqa: E712
    print(activas[["nombre", "sector", "activa"]].head(10))
    print(f"Total activas: {len(activas)}")
    _guardar(activas, 1)
    return activas


def consulta_2(df):
    print("\n--- Consulta 2: Empresas de Logistica, ordenadas por nombre ---")
    logistica = df[df["sector"] == "Logistica"].sort_values("nombre")
    print(logistica[["nombre", "sector"]].head(10))
    print(f"Total en Logistica: {len(logistica)}")
    _guardar(logistica, 2)
    return logistica


def consulta_3(df):
    print("\n--- Consulta 3: ¿Cuantas empresas hay por sector? (value_counts) ---")
    conteo = df["sector"].value_counts()
    print(conteo)
    _guardar(conteo, 3)
    return conteo


def consulta_4(df):
    print("\n--- Consulta 4 (GROUPBY): empresas por sector, de mayor a menor ---")
    por_sector = df.groupby("sector")["id"].count().sort_values(ascending=False)
    print(por_sector)
    _guardar(por_sector, 4)
    return por_sector


def consulta_5(df):
    print("\n--- Consulta 5 (GROUPBY doble): activas e inactivas por sector ---")
    tabla = df.groupby(["sector", "activa"])["id"].count().unstack(fill_value=0)
    print(tabla)
    _guardar(tabla, 5)
    return tabla


def ejecutar_consultas(df):
    """Corre las cinco consultas en orden y devuelve sus resultados."""
    return {
        "activas": consulta_1(df),
        "logistica": consulta_2(df),
        "conteo": consulta_3(df),
        "por_sector": consulta_4(df),
        "tabla": consulta_5(df),
    }


if __name__ == "__main__":
    ejecutar_consultas(cargar())
