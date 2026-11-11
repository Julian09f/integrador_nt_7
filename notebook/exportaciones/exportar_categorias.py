"""Exporta los datos sucios de `categorias` a CSV, Excel y JSON.

Reutiliza `generar_categorias()` de simular_categorias.py (no copia el codigo
de generacion) y guarda el MISMO DataFrame en tres formatos dentro de
datos/crudos/. Siguen sucios a proposito: son la entrada de la etapa de limpieza.

Uso:
    python notebook/exportaciones/exportar_categorias.py
"""

import os
import sys
from importlib import import_module

# Importa la funcion del script anterior sin volver a copiar su codigo
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "simulaciones"))
generar_categorias = import_module("simular_categorias").generar_categorias

# Rutas relativas a la raiz del proyecto (funciona sin importar desde donde se corra)
sys.stdout.reconfigure(encoding="utf-8")  # tildes y ñ en la consola de Windows

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CARPETA_CRUDO = os.path.join(RAIZ, "datos", "crudos")


def exportar_categorias(df):
    """Guarda el DataFrame en CSV, XLSX y JSON y devuelve las rutas creadas."""
    os.makedirs(CARPETA_CRUDO, exist_ok=True)

    ruta_csv = os.path.join(CARPETA_CRUDO, "categorias_sucio.csv")
    ruta_xlsx = os.path.join(CARPETA_CRUDO, "categorias_sucio.xlsx")
    ruta_json = os.path.join(CARPETA_CRUDO, "categorias_sucio.json")

    df.to_csv(ruta_csv, index=False, encoding="utf-8")
    df.to_excel(ruta_xlsx, index=False, sheet_name="categorias")
    df.to_json(ruta_json, orient="records", force_ascii=False, indent=2)

    return [ruta_csv, ruta_xlsx, ruta_json]


if __name__ == "__main__":
    df = generar_categorias()
    for ruta in exportar_categorias(df):
        print(f"{ruta}  ->  shape={df.shape}")
