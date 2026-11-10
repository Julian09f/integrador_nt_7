"""Limpia los datos sucios de `categorias` con pandas.

Lee datos/crudos/categorias_sucio.csv, arregla uno por uno los errores sembrados
en simular_categorias.py (duplicados, nulos, espacios, mayusculas, tildes) y
guarda el resultado en datos/limpios/categorias_limpio.csv.

Regla de oro: ANTES y DESPUES. Se imprime shape, info() y isna().sum() al
empezar y al terminar; esa comparacion es la evidencia de la limpieza.

Uso:
    python notebook/limpieza/limpiar_categorias.py
"""

import os
import sys

import pandas as pd

# Rutas relativas a la raiz del proyecto (funciona sin importar desde donde se corra)
sys.stdout.reconfigure(encoding="utf-8")  # tildes y ñ en la consola de Windows

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUTA_SUCIO = os.path.join(RAIZ, "datos", "crudos", "categorias_sucio.csv")
CARPETA_LIMPIO = os.path.join(RAIZ, "datos", "limpios")
RUTA_LIMPIO = os.path.join(CARPETA_LIMPIO, "categorias_limpio.csv")
RUTA_CATALOGO = os.path.join(CARPETA_LIMPIO, "categorias_catalogo.csv")

COLUMNAS_OBLIGATORIAS = ["id", "nombre", "descripcion", "area_responsable"]


def diagnostico(df, titulo):
    """Imprime shape, info(), nulos y duplicados exactos del DataFrame."""
    print(f"\n===== {titulo} =====")
    print("shape:", df.shape)
    print("\ninfo():")
    df.info()
    print("\nisna().sum():")
    print(df.isna().sum())
    print("\nduplicados exactos:", df.duplicated().sum())


def limpiar_categorias(df):
    """Aplica la limpieza paso a paso y devuelve el DataFrame limpio."""
    # 1) Duplicados exactos
    df = df.drop_duplicates().copy()

    # 2) Unificar el nombre: sin espacios sobrantes y en formato Titulo
    df["nombre"] = df["nombre"].str.strip().str.title()

    # 3) Quitar tildes para que "logística" y "logistica" queden iguales
    df["nombre"] = (
        df["nombre"]
        .str.normalize("NFKD")
        .str.encode("ascii", "ignore")
        .str.decode("utf-8")
    )

    # 4) Rellenar los nulos
    df["descripcion"] = df["descripcion"].fillna("Sin descripcion")
    df["area_responsable"] = df["area_responsable"].fillna("Sin asignar")

    # 5) Nueva columna: largo de la descripcion
    df["largo_desc"] = df["descripcion"].str.len()

    return df


def main():
    if not os.path.exists(RUTA_SUCIO):
        sys.exit(
            f"No existe {RUTA_SUCIO}\n"
            "Genera primero el archivo sucio de categorias (etapa de exportacion)."
        )

    df = pd.read_csv(RUTA_SUCIO)

    # ANTES
    filas_antes = len(df)
    diagnostico(df, "ANTES de limpiar")

    df = limpiar_categorias(df)

    # Catalogo real: una fila por categoria
    catalogo = df.drop_duplicates(subset=["nombre"])

    # Resultado visible de la limpieza
    print(f"\nFilas antes: {filas_antes} | filas despues: {len(df)}")

    # DESPUES
    diagnostico(df, "DESPUES de limpiar")
    print(f"\nFilas eliminadas: {filas_antes - len(df)}")

    # Garantias: ningun nulo en columnas obligatorias ni duplicados exactos
    assert df[COLUMNAS_OBLIGATORIAS].isna().sum().sum() == 0, "Quedaron nulos"
    assert df.duplicated().sum() == 0, "Quedaron duplicados exactos"

    # Guardar resultados
    os.makedirs(CARPETA_LIMPIO, exist_ok=True)
    df.to_csv(RUTA_LIMPIO, index=False, encoding="utf-8")
    # Tambien en JSON y Excel (los "limpios" del tablero: CSV, JSON y XLSX)
    df.to_json(RUTA_LIMPIO.replace(".csv", ".json"), orient="records", force_ascii=False, indent=2)
    df.to_excel(RUTA_LIMPIO.replace(".csv", ".xlsx"), index=False, sheet_name="categorias")
    catalogo.to_csv(RUTA_CATALOGO, index=False, encoding="utf-8")
    print(f"\nGuardado: {RUTA_LIMPIO}  shape={df.shape}")
    print(f"Guardado: {RUTA_CATALOGO}  shape={catalogo.shape}")


if __name__ == "__main__":
    main()
