#!/usr/bin/env python3
"""
reportar_retos.py - HU G01: tres gráficas sobre la tabla retos (proyecto integrador).

Uso (desde cualquier carpeta o con el botón Play):
    python reportar_retos.py [ruta/a/retos_limpio.csv]

Lee el CSV LIMPIO (por defecto datos/limpios/retos_limpio.csv, separador ";", generado por
notebook/limpieza/limpiar_retos.py), calcula duracion_dias = fecha_fin - fecha_inicio,
genera tres gráficas con matplotlib en datos/reportes/ (dpi=120), imprime la ruta de cada una y las conclusiones.

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
except ImportError as error:
    sys.stderr.write(f"ERROR: falta una dependencia ({error.name}). Instala: pip install pandas matplotlib\n")
    sys.exit(1)

CARPETA_PROYECTO = Path(__file__).resolve().parents[2]
CARPETA_REPORTES = CARPETA_PROYECTO / "datos" / "reportes"
RUTA_POR_DEFECTO = CARPETA_PROYECTO / "datos" / "limpios" / "retos_limpio.csv"
COLUMNAS_REQUERIDAS = ("id", "estado", "fecha_inicio", "fecha_fin")
SEPARADOR = ";"  # limpiar_retos.py exporta con ";"
TAMANO_MAXIMO_BYTES = 50 * 1024 * 1024  # límite defensivo: 50 MB
DPI = 120
MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre")


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
    """Lee el CSV, verifica columnas obligatorias y normaliza estado, fechas y duración."""
    df = pd.read_csv(ruta, sep=SEPARADOR, encoding="utf-8-sig", dtype=str)  # limpiar_retos.py exporta con BOM
    df.columns = df.columns.str.strip()

    faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas obligatorias: {', '.join(faltantes)}")
    if df.empty:
        raise ValueError("El CSV no tiene filas de datos")

    df["estado"] = df["estado"].str.strip().str.upper()
    for col in ("fecha_inicio", "fecha_fin"):
        df[col] = pd.to_datetime(df[col], errors="coerce", format="ISO8601")
    # duracion_dias no existe en la tabla retos: se deriva de las fechas (vacía si no hay fecha_fin)
    df["duracion_dias"] = (df["fecha_fin"] - df["fecha_inicio"]).dt.days

    # Avisos por stderr: retos sin fecha_fin (permitido) y datos que la limpieza no debió dejar pasar
    avisos = {
        "estado vacío": int(df["estado"].isna().sum()),
        "fecha_fin vacía (sin duracion_dias)": int(df["duracion_dias"].isna().sum()),
        "fecha_inicio inválida": int(df["fecha_inicio"].isna().sum()),
    }
    for descripcion, cantidad in avisos.items():
        if cantidad:
            sys.stderr.write(f"AVISO: {cantidad} fila(s) con {descripcion} (se excluyen donde aplica)\n")
    return df


def filtrar_duraciones_validas(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve solo filas con duración numérica >= 0 (las negativas son fechas invertidas)."""
    return df[df["duracion_dias"].notna() & (df["duracion_dias"] >= 0)]


def calcular_retos_por_mes(df: pd.DataFrame) -> pd.Series:
    """Cuenta retos por mes de inicio e incluye en 0 los meses intermedios sin retos."""
    con_fecha = df[df["fecha_inicio"].notna()]
    if con_fecha.empty:
        raise ValueError("No hay fechas de inicio válidas para la gráfica por mes")
    por_mes = con_fecha.groupby(con_fecha["fecha_inicio"].dt.to_period("M"))["id"].count()
    rango = pd.period_range(por_mes.index.min(), por_mes.index.max(), freq="M")
    return por_mes.reindex(rango, fill_value=0)


def guardar_grafica(numero: int) -> str:
    """Aplica tight_layout, guarda la figura actual en reportes/ con dpi=120 y la cierra."""
    ruta = CARPETA_REPORTES / f"retos_grafica_{numero}.png"
    plt.tight_layout()
    try:
        plt.savefig(ruta, dpi=DPI)
    finally:
        plt.close()  # libera memoria aunque falle el guardado
    return str(ruta)


def grafica_barras_estado(df: pd.DataFrame) -> str:
    """Gráfica 1: barras con la cantidad de retos por estado."""
    conteo = df["estado"].value_counts()
    plt.figure(figsize=(8, 5))
    conteo.plot(kind="bar")
    plt.title("Cantidad de retos por estado")
    plt.xlabel("Estado")
    plt.ylabel("Cantidad de retos")
    plt.xticks(rotation=0)
    return guardar_grafica(1)


def grafica_linea_mes(por_mes: pd.Series) -> str:
    """Gráfica 2: línea con los retos que empiezan cada mes."""
    serie = por_mes.copy()
    serie.index = serie.index.astype(str)  # etiquetas legibles AAAA-MM
    plt.figure(figsize=(8, 5))
    serie.plot(kind="line", marker="o")
    plt.title("Retos que empiezan cada mes")
    plt.xlabel("Mes de inicio")
    plt.ylabel("Cantidad de retos")
    plt.xticks(range(len(serie)), serie.index, rotation=45)
    return guardar_grafica(2)


def grafica_histograma_duracion(df_validos: pd.DataFrame) -> str:
    """Gráfica 3: histograma de cómo se reparte la duración de los retos (solo duraciones válidas)."""
    if df_validos.empty:
        raise ValueError("No hay duraciones válidas para el histograma")
    plt.figure(figsize=(8, 5))
    df_validos["duracion_dias"].plot(kind="hist", bins=20)
    plt.title("Distribución de la duración de los retos")
    plt.xlabel("Duración (días)")
    plt.ylabel("Cantidad de retos")
    return guardar_grafica(3)


def construir_conclusiones(df: pd.DataFrame, df_validos: pd.DataFrame, por_mes: pd.Series) -> list:
    """Arma el texto de conclusiones: mes pico, duración promedio por estado y fechas invertidas."""
    lineas = []

    # 1. Mes con más retos (puede haber empate)
    maximo = int(por_mes.max())
    picos = [f"{MESES[p.month - 1]} {p.year}" for p in por_mes[por_mes == maximo].index]
    lineas.append(f"1. Los retos se concentran en {', '.join(picos)} ({maximo} retos de {int(por_mes.sum())}).")
    lineas.append("   Posible causa (hipótesis, validar con el negocio): inicio de periodo académico o "
                  "planeación de trimestre, cuando se lanzan más retos a la vez.")

    # 2. Duración promedio por estado (sin duraciones negativas ni vacías)
    promedio = df_validos.groupby("estado")["duracion_dias"].agg(["count", "mean"]).sort_values("mean", ascending=False)
    lineas.append("2. Duración promedio por estado (solo duraciones válidas):")
    for estado, fila in promedio.iterrows():
        lineas.append(f"   - {estado}: {fila['mean']:.1f} días ({int(fila['count'])} retos)")
    lineas.append(f"   - General: {df_validos['duracion_dias'].mean():.1f} días")

    # 3. Fechas invertidas (dato para el back)
    ambas = df["fecha_inicio"].notna() & df["fecha_fin"].notna()
    invertidas = df[ambas & (df["fecha_fin"] < df["fecha_inicio"])]
    ids = ", ".join(invertidas["id"].astype(str)) or "ninguno"
    lineas.append(f"3. Retos con fecha_fin antes de fecha_inicio: {len(invertidas)} (ids: {ids}).")
    lineas.append("   Dato para el back: validar fecha_fin >= fecha_inicio al crear/editar un reto.")

    excluidos = len(df) - len(df_validos)
    if excluidos:
        lineas.append(f"Nota: {excluidos} reto(s) quedaron fuera de promedios e histograma por duración vacía o negativa.")
    return lineas


def main() -> int:
    """Punto de entrada: valida argumentos, genera las tres gráficas e imprime rutas y conclusiones."""
    # Consola de Windows (cp1252) muestra mal tildes y ñ: forzar UTF-8 en la salida
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="HU G01: gráficas de la tabla retos")
    parser.add_argument("csv", nargs="?", default=str(RUTA_POR_DEFECTO),
                        help="Ruta a retos_limpio.csv (por defecto datos/limpios/retos_limpio.csv)")
    args = parser.parse_args()

    try:
        df = cargar_datos(validar_ruta(args.csv))
        df_validos = filtrar_duraciones_validas(df)
        por_mes = calcular_retos_por_mes(df)
    except (FileNotFoundError, ValueError, UnicodeDecodeError, pd.errors.ParserError) as error:
        sys.stderr.write(f"ERROR: {error}\n")
        return 1

    try:
        CARPETA_REPORTES.mkdir(parents=True, exist_ok=True)
        rutas = [
            grafica_barras_estado(df),
            grafica_linea_mes(por_mes),
            grafica_histograma_duracion(df_validos),
        ]
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
    for linea in construir_conclusiones(df, df_validos, por_mes):
        print(linea)
    return 0


if __name__ == "__main__":
    sys.exit(main())