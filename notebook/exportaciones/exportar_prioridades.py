"""Exporta el DataFrame sucio de prioridades a CSV, Excel y JSON.

Importa generar_prioridades() desde el generador real del proyecto
(y no copia su código) y guarda el mismo DataFrame en la carpeta
`datos/crudos/` en tres formatos. Estos archivos siguen sucios y son la
entrada de la etapa de limpieza.

Uso (desde la raíz del proyecto):
    python notebook/exportaciones/exportar_prioridades.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from notebook.simulaciones.simular_prioridades import generar_prioridades

CARPETA = ROOT / "datos" / "crudos"
BASE = "prioridades_sucio"


def main() -> None:
    df = generar_prioridades()

    CARPETA.mkdir(parents=True, exist_ok=True)

    ruta_csv = CARPETA / f"{BASE}.csv"
    ruta_xlsx = CARPETA / f"{BASE}.xlsx"
    ruta_json = CARPETA / f"{BASE}.json"

    df.to_csv(ruta_csv, index=False, encoding="utf-8")
    df.to_excel(ruta_xlsx, index=False, sheet_name="prioridades")
    df.to_json(ruta_json, orient="records", force_ascii=False, indent=2)

    print("Archivos generados:")
    for ruta in (ruta_csv, ruta_xlsx, ruta_json):
        print(f"  {ruta}  ->  shape={df.shape}")


if __name__ == "__main__":
    main()
