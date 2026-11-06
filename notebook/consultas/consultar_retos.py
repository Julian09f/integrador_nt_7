#!/usr/bin/env python3
"""
consultar_retos.py - HU Q01: cinco consultas sobre la tabla retos (proyecto integrador).

Uso (desde la raíz del proyecto, después de notebook/limpieza/limpiar_retos.py):
    python notebook/consultas/consultar_retos.py [data/limpio/retos_limpio.csv]

Lee el CSV LIMPIO (por defecto data/limpio/retos_limpio.csv), resuelve cinco consultas
(dos con groupby), imprime título y resultado de cada una en orden y guarda
retos_consulta_N.csv (UTF-8 con BOM, legible en Excel) en la misma carpeta del archivo de entrada.

Códigos de salida: 0 = OK, 1 = error de entrada/datos, 2 = error de escritura.
"""

import argparse
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:  # pandas es la única dependencia externa
    sys.stderr.write("ERROR: falta pandas. Instálalo con: pip install pandas\n")
    sys.exit(1)

COLUMNAS_REQUERIDAS = ("id", "nombre", "estado", "duracion_dias", "fecha_inicio")
RUTA_POR_DEFECTO = Path(__file__).resolve().parents[2] / "data" / "limpio" / "retos_limpio.csv"
CODIFICACION = "utf-8-sig"  # lee CSV con o sin BOM y escribe con BOM para que Excel muestre tildes
TAMANO_MAXIMO_BYTES = 50 * 1024 * 1024  # límite defensivo: 50 MB
PREFIJOS_FORMULA = ("=", "+", "-", "@", "\t", "\r")  # OWASP CSV Injection


def validar_ruta(ruta_texto: str) -> Path:
    """Valida que la ruta exista, sea un archivo .csv legible y no exceda el tamaño máximo."""
    ruta = Path(ruta_texto).expanduser().resolve()
    if ruta.suffix.lower() != ".csv":
        raise ValueError(f"El archivo debe tener extensión .csv: {ruta.name}")
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el archivo: {ruta}")
    if ruta.stat().st_size == 0:
        raise ValueError(f"El archivo está vacío: {ruta.name}")
    if ruta.stat().st_size > TAMANO_MAXIMO_BYTES:
        raise ValueError(f"El archivo supera {TAMANO_MAXIMO_BYTES // (1024 * 1024)} MB")
    return ruta


def cargar_datos(ruta: Path) -> pd.DataFrame:
    """Lee el CSV limpio, verifica columnas obligatorias y normaliza tipos (número y fecha)."""
    df = pd.read_csv(ruta, encoding=CODIFICACION)
    df.columns = df.columns.str.strip()

    faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas obligatorias: {', '.join(faltantes)}")
    if df.empty:
        raise ValueError("El CSV no tiene filas de datos")

    df["estado"] = df["estado"].astype("string").str.strip().str.upper()
    df["duracion_dias"] = pd.to_numeric(df["duracion_dias"], errors="coerce")
    df["fecha_inicio"] = pd.to_datetime(df["fecha_inicio"], errors="coerce", format="ISO8601")

    # Avisos (stderr) para datos que el limpieza previa no debió dejar pasar
    sin_duracion = int(df["duracion_dias"].isna().sum())
    sin_fecha = int(df["fecha_inicio"].isna().sum())
    if sin_duracion:
        sys.stderr.write(f"AVISO: {sin_duracion} fila(s) con duracion_dias vacía o no numérica (se excluyen donde aplica)\n")
    if sin_fecha:
        sys.stderr.write(f"AVISO: {sin_fecha} fila(s) con fecha_inicio inválida (se excluyen de la consulta 5)\n")
    return df


def neutralizar_formulas(datos: pd.DataFrame) -> pd.DataFrame:
    """Antepone ' a textos que empiezan por =,+,-,@ para evitar inyección de fórmulas al abrir el CSV en Excel."""
    seguro = datos.copy()
    for col in seguro.columns:
        if seguro[col].dtype == object or pd.api.types.is_string_dtype(seguro[col]):
            seguro[col] = seguro[col].map(
                lambda v: f"'{v}" if isinstance(v, str) and v.startswith(PREFIJOS_FORMULA) else v
            )
    return seguro


def guardar_resultado(resultado, carpeta: Path, numero: int) -> Path:
    """Guarda el resultado (DataFrame o Series) como retos_consulta_N.csv en UTF-8 con BOM."""
    datos = resultado.to_frame() if isinstance(resultado, pd.Series) else resultado
    if datos.index.name is not None:  # índice con significado (estado, mes) -> pasa a columna
        datos = datos.reset_index()
    destino = carpeta / f"retos_consulta_{numero}.csv"
    neutralizar_formulas(datos).to_csv(destino, index=False, encoding=CODIFICACION)
    return destino


def mostrar(titulo: str, resultado) -> None:
    """Imprime el título de la consulta y su resultado completo, sin truncar filas ni columnas."""
    print(f"\n=== {titulo} ===")
    with pd.option_context("display.max_rows", None, "display.max_columns", None, "display.width", 200):
        print(resultado if len(resultado) else "(sin resultados)")


def consulta_1(df: pd.DataFrame, carpeta: Path) -> pd.DataFrame:
    """Consulta 1: retos cuyo estado es EN_CURSO (columnas clave, para que no se trunquen)."""
    en_curso = df.loc[df["estado"] == "EN_CURSO", list(COLUMNAS_REQUERIDAS)]
    mostrar("Consulta 1 - Retos que están en curso", en_curso)
    guardar_resultado(en_curso, carpeta, 1)
    return en_curso


def consulta_2(df: pd.DataFrame, carpeta: Path) -> pd.DataFrame:
    """Consulta 2: los 10 retos con mayor duracion_dias (nlargest ignora NaN)."""
    largos = df.nlargest(10, "duracion_dias")[["nombre", "duracion_dias", "estado"]]
    mostrar("Consulta 2 - Los 10 retos más largos", largos)
    guardar_resultado(largos, carpeta, 2)
    return largos


def consulta_3(df: pd.DataFrame, carpeta: Path) -> pd.Series:
    """Consulta 3: cantidad de retos por estado con value_counts."""
    conteo = df["estado"].value_counts()
    mostrar("Consulta 3 - Cuántos retos hay por estado", conteo)
    guardar_resultado(conteo, carpeta, 3)
    return conteo


def consulta_4(df: pd.DataFrame, carpeta: Path) -> pd.DataFrame:
    """Consulta 4 (GROUPBY): conteo, duración promedio, mínima y máxima por estado."""
    resumen = df.groupby("estado")["duracion_dias"].agg(["count", "mean", "min", "max"]).round(2)
    mostrar("Consulta 4 - GROUPBY: duración promedio, mínima y máxima por estado", resumen)
    guardar_resultado(resumen, carpeta, 4)
    return resumen


def consulta_5(df: pd.DataFrame, carpeta: Path) -> pd.Series:
    """Consulta 5 (GROUPBY por mes): cuántos retos empiezan cada mes (periodo AAAA-MM)."""
    por_mes = df.groupby(df["fecha_inicio"].dt.to_period("M"))["id"].count()
    mostrar("Consulta 5 - GROUPBY por mes: cuántos retos empiezan cada mes", por_mes)
    guardar_resultado(por_mes, carpeta, 5)
    return por_mes


def main() -> int:
    """Punto de entrada: valida argumentos, carga datos y ejecuta las cinco consultas en orden."""
    for flujo in (sys.stdout, sys.stderr):  # tildes correctas también en consolas cp1252 / Git Bash
        flujo.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="HU Q01 - Consultas sobre retos_limpio.csv")
    parser.add_argument("ruta_csv", nargs="?", default=str(RUTA_POR_DEFECTO),
                        help="Ruta a retos_limpio.csv (por defecto data/limpio/retos_limpio.csv)")
    args = parser.parse_args()

    try:
        ruta = validar_ruta(args.ruta_csv)
        df = cargar_datos(ruta)
    except (FileNotFoundError, ValueError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        return 1

    carpeta = ruta.parent
    try:
        for consulta in (consulta_1, consulta_2, consulta_3, consulta_4, consulta_5):
            consulta(df, carpeta)
    except OSError as exc:
        sys.stderr.write(f"ERROR al escribir resultados: {exc}\n")
        return 2

    print(f"\nResultados guardados en: {carpeta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())