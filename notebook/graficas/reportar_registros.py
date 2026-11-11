#!/usr/bin/env python3
"""
reportar_registros.py - HU G01: tres gráficas sobre la tabla registros (proyecto integrador).

Uso (desde cualquier carpeta o con el botón Play):
    python reportar_registros.py [ruta/a/registros_limpio.csv]

Lee el CSV LIMPIO (por defecto datos/limpios/registros_limpio.csv, generado por
notebook/limpieza/limpiar_registros.py), genera tres gráficas con matplotlib en
datos/reportes/ (dpi=120), imprime la ruta de cada una y las conclusiones.

Códigos de salida: 0 = OK, 1 = error de entrada/datos, 2 = error al guardar.
"""

import argparse
import sys
from pathlib import Path

try:
    import pandas as pd
    import matplotlib

    matplotlib.use("Agg")  # backend sin ventana: el script nunca se queda esperando
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
except ImportError as error:
    sys.stderr.write(f"ERROR: falta una dependencia ({error.name}). Instala: pip install pandas matplotlib\n")
    sys.exit(1)

CARPETA_PROYECTO = Path(__file__).resolve().parents[2]
CARPETA_REPORTES = CARPETA_PROYECTO / "datos" / "reportes"
RUTA_POR_DEFECTO = CARPETA_PROYECTO / "datos" / "limpios" / "registros_limpio.csv"
TAMANO_MAXIMO_BYTES = 50 * 1024 * 1024  # límite defensivo: 50 MB
DPI = 120
MESES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
)


def abreviar_reto(nombre: str) -> str:
    """Abrevia identificadores largos (como UUIDs) para que se vean legibles en los gráficos."""
    texto = str(nombre).strip()
    if len(texto) > 16 and "-" in texto:
        return f"Reto {texto[:8]}..."
    return texto


def validar_ruta(ruta_texto: str) -> Path:
    """Valida que la ruta exista, sea un .csv, no esté vacía y no supere el tamaño máximo."""
    ruta = Path(ruta_texto).expanduser().resolve()
    if ruta.suffix.lower() != ".csv":
        raise ValueError(f"El archivo debe tener extensión .csv: {ruta.name}")
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el archivo: {ruta}")
    tamano = ruta.stat().st_size
    if tamano == 0:
        raise ValueError(f"El archivo está vacío: {ruta.name}")
    if tamano > TAMANO_MAXIMO_BYTES:
        raise ValueError(f"El archivo supera {TAMANO_MAXIMO_BYTES // (1024 * 1024)} MB")
    return ruta


def cargar_datos(ruta: Path) -> pd.DataFrame:
    """Lee el CSV limpio, verifica columnas requeridas y normaliza fechas, estados y referencias."""
    try:
        df = pd.read_csv(ruta, sep=None, engine="python", encoding="utf-8-sig", dtype=str)
    except Exception:
        df = pd.read_csv(ruta, encoding="utf-8-sig", dtype=str)

    df.columns = df.columns.str.strip()
    if df.empty:
        raise ValueError("El CSV no tiene filas de datos")

    # Mapeo flexible de columnas para soportar variantes de nombres
    col_fecha = next((c for c in ("fecha_registro", "fecha_inscripcion", "fecha") if c in df.columns), None)
    if not col_fecha:
        raise ValueError("Falta columna de fecha ('fecha_registro' o 'fecha_inscripcion') en el CSV")
    df["fecha_normalizada"] = pd.to_datetime(df[col_fecha], errors="coerce")

    if "estado" not in df.columns:
        raise ValueError("Falta la columna 'estado' en el CSV")
    df["estado_normalizado"] = df["estado"].fillna("SIN DEFINIR").astype(str).str.strip().str.title()

    col_usuario = next((c for c in ("id_usuario", "id_participante", "usuario") if c in df.columns), None)
    if not col_usuario:
        col_usuario = "id"
    df["usuario_normalizado"] = df[col_usuario].astype(str).str.strip()

    col_reto = next((c for c in ("nombre_reto", "id_reto", "reto") if c in df.columns), None)
    if not col_reto:
        raise ValueError("Falta columna de reto ('nombre_reto' o 'id_reto') en el CSV")
    df["reto_normalizado"] = df[col_reto].astype(str).str.strip()

    # Avisos informativos por stderr si hay fechas nulas
    nulos_fecha = int(df["fecha_normalizada"].isna().sum())
    if nulos_fecha:
        sys.stderr.write(f"AVISO: {nulos_fecha} fila(s) con fecha no válida (se excluyen en gráfica por mes)\n")

    return df


def guardar_grafica(numero: int) -> str:
    """Aplica tight_layout, guarda la figura actual en datos/reportes/ con dpi=120 y la cierra."""
    ruta = CARPETA_REPORTES / f"registros_grafica_{numero}.png"
    plt.tight_layout()
    try:
        plt.savefig(ruta, dpi=DPI)
    finally:
        plt.close()
    return str(ruta)


def grafica_barras_estado(df: pd.DataFrame) -> str:
    """Gráfica 1 (barras): cantidad de participaciones por estado."""
    conteo = df["estado_normalizado"].value_counts()
    plt.figure(figsize=(8, 5))
    conteo.plot(kind="bar")
    plt.title("Participaciones por estado")
    plt.xlabel("Estado")
    plt.ylabel("Cantidad de participaciones")
    plt.xticks(rotation=0)
    return guardar_grafica(1)


def grafica_linea_mes(df: pd.DataFrame) -> tuple[str, pd.Series]:
    """Gráfica 2 (línea): cantidad de participaciones por mes."""
    con_fecha = df[df["fecha_normalizada"].notna()]
    if con_fecha.empty:
        raise ValueError("No hay fechas válidas para la gráfica por mes")

    por_mes = con_fecha.groupby(con_fecha["fecha_normalizada"].dt.to_period("M")).size()
    rango = pd.period_range(por_mes.index.min(), por_mes.index.max(), freq="M")
    por_mes = por_mes.reindex(rango, fill_value=0)

    serie = por_mes.copy()
    serie.index = serie.index.astype(str)

    plt.figure(figsize=(8, 5))
    serie.plot(kind="line", marker="o")
    plt.title("Participaciones por mes")
    plt.xlabel("Mes de inscripción")
    plt.ylabel("Cantidad de participaciones")
    plt.xticks(range(len(serie)), serie.index, rotation=45)
    return guardar_grafica(2), por_mes


def grafica_top_retos(df: pd.DataFrame) -> tuple[str, pd.Series]:
    """Gráfica 3 (barras horizontales): los 10 retos con más participantes."""
    top_retos = (
        df.groupby("reto_normalizado")["usuario_normalizado"]
        .nunique()
        .sort_values(ascending=False)
        .head(10)
    )
    if top_retos.empty:
        raise ValueError("No hay datos para calcular el top de retos")

    serie_plot = top_retos.sort_values().copy()
    serie_plot.index = [abreviar_reto(str(idx)) for idx in serie_plot.index]

    plt.figure(figsize=(9, 5.5))
    serie_plot.plot(kind="barh")
    plt.title("Top 10 retos con más participantes")
    plt.xlabel("Cantidad de participantes")
    plt.ylabel("Reto")
    plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
    return guardar_grafica(3), top_retos


def contar_duplicados(df: pd.DataFrame) -> int:
    """Cuenta inscripciones repetidas (mismo participante en el mismo reto)."""
    return int(df.duplicated(subset=["usuario_normalizado", "reto_normalizado"], keep="first").sum())


def construir_conclusiones(df: pd.DataFrame, por_mes: pd.Series, top_retos: pd.Series) -> list[str]:
    """Construye las conclusiones requeridas por los criterios de aceptación de la HU G01."""
    lineas = []

    # 1. Reto más popular
    reto_popular = top_retos.index[0]
    participantes_reto = int(top_retos.iloc[0])
    nombre_mostrar = abreviar_reto(str(reto_popular))
    if nombre_mostrar != str(reto_popular):
        desc_reto = f"'{nombre_mostrar}' (ID: {reto_popular})"
    else:
        desc_reto = f"'{reto_popular}'"
    lineas.append(f"1. El reto más popular es {desc_reto} con {participantes_reto} participantes.")

    # 2. Mes con más inscripciones
    mes_max = por_mes.idxmax()
    inscripciones_mes = int(por_mes.max())
    nombre_mes = f"{MESES[mes_max.month - 1]} {mes_max.year}"
    lineas.append(f"2. El mes con más inscripciones fue {nombre_mes} ({mes_max}) con {inscripciones_mes} inscripciones.")

    # 3. Inscripciones duplicadas y bloqueo HTTP 409
    duplicados = contar_duplicados(df)
    lineas.append(f"3. Se encontraron {duplicados} inscripciones duplicadas (mismo usuario en el mismo reto).")
    lineas.append(
        "   El backend debe bloquearlas con 409 Conflict: la petición es válida, pero entra en conflicto\n"
        "   con un registro ya existente en la base de datos. Esto protege la integridad de los datos,\n"
        "   evita inflar las estadísticas y no delega la seguridad en el frontend."
    )

    return lineas


def main() -> int:
    """Punto de entrada: valida argumentos, genera las tres gráficas e imprime rutas y conclusiones."""
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="HU G01: tres gráficas sobre la tabla registros")
    parser.add_argument(
        "csv",
        nargs="?",
        default=str(RUTA_POR_DEFECTO),
        help="Ruta a registros_limpio.csv (por defecto datos/limpios/registros_limpio.csv)",
    )
    args = parser.parse_args()

    try:
        ruta_archivo = validar_ruta(args.csv)
        df = cargar_datos(ruta_archivo)
    except (FileNotFoundError, ValueError, UnicodeDecodeError, pd.errors.ParserError) as error:
        sys.stderr.write(f"ERROR: {error}\n")
        return 1

    try:
        CARPETA_REPORTES.mkdir(parents=True, exist_ok=True)
        ruta_g1 = grafica_barras_estado(df)
        ruta_g2, por_mes = grafica_linea_mes(df)
        ruta_g3, top_retos = grafica_top_retos(df)
        rutas = [ruta_g1, ruta_g2, ruta_g3]
    except ValueError as error:
        sys.stderr.write(f"ERROR: {error}\n")
        return 1
    except OSError as error:
        sys.stderr.write(f"ERROR al guardar las gráficas: {error}\n")
        return 2

    print("Gráficas generadas:")
    for ruta in rutas:
        print(f"  {ruta}")
    print("\nConclusiones:")
    for linea in construir_conclusiones(df, por_mes, top_retos):
        print(linea)

    return 0


if __name__ == "__main__":
    sys.exit(main())
