"""Limpia los datos sucios de `empresas` con pandas.

Lee datos/crudos/empresas_sucio.csv, arregla UNO POR UNO los errores sembrados
en simular_empresas.py y guarda datos/limpios/empresas_limpio.csv.

Regla de oro: ANTES y DESPUES (shape, info, nulos).

Uso:
    python notebook/limpieza/limpiar_empresas.py
"""

import os
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")  # tildes y ñ en la consola de Windows

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUTA_SUCIO = os.path.join(RAIZ, "datos", "crudos", "empresas_sucio.csv")
CARPETA_LIMPIO = os.path.join(RAIZ, "datos", "limpios")
RUTA_LIMPIO = os.path.join(CARPETA_LIMPIO, "empresas_limpio.csv")

# Valores de texto que significan True / False en la columna `activa`
MAPA_ACTIVA = {
    "TRUE": True, "SI": True, "SÍ": True, "1": True, "1.0": True,
    "FALSE": False, "NO": False, "0": False, "0.0": False,
}


def diagnostico(df, titulo):
    """Imprime shape, info() y nulos: es la evidencia del antes/despues."""
    print(f"\n===== {titulo} =====")
    print("shape:", df.shape)
    df.info()
    print("\nNulos por columna:")
    print(df.isna().sum())
    print("Duplicados exactos:", df.duplicated().sum())


def limpiar_empresas(df):
    """Aplica todas las reglas de limpieza y devuelve un DataFrame nuevo."""
    # 1) Duplicados exactos
    df = df.drop_duplicates().copy()

    # 2) Espacios sobrantes en el nombre y unificar MAYUSCULAS -> Titulo
    df["nombre"] = df["nombre"].str.strip()
    en_mayusculas = df["nombre"].str.isupper()
    df.loc[en_mayusculas, "nombre"] = df.loc[en_mayusculas, "nombre"].str.title()

    # 3) Sector: 'LOGISTICA' y ' logistica ' quedan como 'Logistica'
    df["sector"] = df["sector"].str.strip().str.title()

    # 4) NIT en un solo formato (solo digitos)
    df["nit"] = df["nit"].astype(str).str.replace(r"[.\-]", "", regex=True)

    # 5) Telefono solo con digitos (y sin el indicativo +57 -> 10 digitos)
    df["telefono"] = df["telefono"].astype(str).str.replace(r"\D", "", regex=True)
    con_indicativo = (df["telefono"].str.len() == 12) & df["telefono"].str.startswith("57")
    df.loc[con_indicativo, "telefono"] = df.loc[con_indicativo, "telefono"].str[2:]

    # 6) `activa` llega como TEXTO desde el CSV -> booleano de verdad
    df["activa"] = df["activa"].astype(str).str.strip().str.upper().map(MAPA_ACTIVA)
    df["activa"] = df["activa"].astype(bool)

    # 7) Contactos vacios
    df["contacto"] = df["contacto"].fillna("Sin contacto")

    # 8) Correos invalidos: se marcan en una columna nueva
    df["correo_valido"] = df["correo"].str.contains("@", na=False)

    # 9) Por si la limpieza dejo filas repetidas (mismo id)
    df = df.drop_duplicates(subset="id")
    return df.reset_index(drop=True)


if __name__ == "__main__":
    sucio = pd.read_csv(RUTA_SUCIO, dtype=str)  # todo como texto: se convierte a mano
    diagnostico(sucio, "ANTES de limpiar")

    limpio = limpiar_empresas(sucio)
    diagnostico(limpio, "DESPUES de limpiar")

    print(f"\nFilas eliminadas: {len(sucio) - len(limpio)}")
    print(f"Correos invalidos marcados: {(~limpio['correo_valido']).sum()}")
    repetidos = limpio['nit'].duplicated(keep=False).sum()
    print(f"Aviso: {repetidos} filas comparten NIT con otra empresa distinta "
          "(error sembrado; se conserva y queda como hallazgo).")

    os.makedirs(CARPETA_LIMPIO, exist_ok=True)
    limpio.to_csv(RUTA_LIMPIO, index=False, encoding="utf-8")
    # Tambien en JSON y Excel (los "limpios" del tablero: CSV, JSON y XLSX)
    limpio.to_json(RUTA_LIMPIO.replace(".csv", ".json"), orient="records", force_ascii=False, indent=2)
    limpio.to_excel(RUTA_LIMPIO.replace(".csv", ".xlsx"), index=False, sheet_name="empresas")
    print(f"\nGuardado: {RUTA_LIMPIO}  shape={limpio.shape}")
