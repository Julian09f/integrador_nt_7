"""HU X01 - Exporta la tabla `retos` sucia a CSV, Excel y JSON.

Ejecutar desde la raiz del proyecto:
    python notebook/exportaciones/exportar_retos.py   (o la ruta donde quede el script)
Genera <raiz>/data/crudo/retos_sucio.{csv,xlsx,json}. No duplica la logica de
generacion: importa generar_retos() desde simular_retos.py, que puede estar en
la misma carpeta (src/) o en la carpeta hermana simulaciones/ (notebook/).
"""
import os
import sys
from importlib import import_module
from pathlib import Path

NOMBRE_ARCHIVO = "retos_sucio"
FILAS_ESPERADAS = 500
COLUMNAS_HU = ["id", "nombre", "descripcion", "fecha_inicio", "fecha_fin",
               "estado", "id_empresa", "id_categoria", "id_prioridad"]
MARCADORES_RAIZ = ("requirements.txt", ".git")

CARPETA_SCRIPT = Path(__file__).resolve().parent


def encontrar_raiz(desde):
    """Sube carpetas hasta la raiz del proyecto (la que tiene requirements.txt o .git)."""
    for carpeta in (desde, *desde.parents):
        if any((carpeta / m).exists() for m in MARCADORES_RAIZ):
            return carpeta
    raise FileNotFoundError("no se encontro la raiz del proyecto (requirements.txt o .git)")


def cargar_generador():
    """Importa generar_retos() buscando simular_retos.py en ubicaciones conocidas."""
    candidatas = [CARPETA_SCRIPT, CARPETA_SCRIPT.parent / "simulaciones"]
    for carpeta in candidatas:
        if (carpeta / "simular_retos.py").is_file():
            if str(carpeta) not in sys.path:
                sys.path.insert(0, str(carpeta))
            modulo = import_module("simular_retos")
            if not callable(getattr(modulo, "generar_retos", None)):
                raise AttributeError("simular_retos.py no define generar_retos(n=500)")
            return modulo.generar_retos
    raise ImportError(f"no se encontro simular_retos.py en: {[str(c) for c in candidatas]}")


def validar_df(df):
    """Verifica que lo que se va a exportar tenga la forma que pide la HU."""
    faltan = [c for c in COLUMNAS_HU if c not in df.columns]
    if faltan:
        raise ValueError(f"faltan columnas de la HU: {faltan}")
    if len(df) < FILAS_ESPERADAS:
        raise ValueError(f"se esperaban al menos {FILAS_ESPERADAS} filas, llegaron {len(df)}")


def exportar(df, carpeta):
    """Escribe los tres formatos con los parametros exactos de la HU X01."""
    os.makedirs(carpeta, exist_ok=True)
    rutas = {
        "csv": carpeta / f"{NOMBRE_ARCHIVO}.csv",
        "xlsx": carpeta / f"{NOMBRE_ARCHIVO}.xlsx",
        "json": carpeta / f"{NOMBRE_ARCHIVO}.json",
    }
    df.to_csv(rutas["csv"], index=False, encoding="utf-8")
    df.to_excel(rutas["xlsx"], index=False, sheet_name="retos")
    df.to_json(rutas["json"], orient="records", force_ascii=False, indent=2)
    return rutas


def main():
    try:
        raiz = encontrar_raiz(CARPETA_SCRIPT)
        generar_retos = cargar_generador()
        df = generar_retos(n=FILAS_ESPERADAS)
        validar_df(df)
        rutas = exportar(df, raiz / "data" / "crudo")
    except (ImportError, AttributeError, ValueError, FileNotFoundError) as exc:
        print(f"ERROR de datos/importacion: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:  # permisos, disco lleno, archivo abierto en Excel, etc.
        print(f"ERROR al escribir archivos: {exc}", file=sys.stderr)
        return 2

    for ruta in rutas.values():
        print(f"{ruta.relative_to(raiz)} -> shape {df.shape} ({ruta.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())