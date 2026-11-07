"""HU Q01 - Consultas sobre la tabla registros (archivo LIMPIO).

Uso:
    python notebook/consultas/consultar_registros.py [ruta/a/registros_limpio.csv]

Resuelve cinco consultas con pandas, cada una en su propia funcion.
Imprime el titulo y el resultado de cada una y guarda
registros_consulta_N.csv en la carpeta del archivo limpio.
"""

import os
import sys
from pathlib import Path
import pandas as pd

# Agrega la raiz del proyecto al path
sys.path.append(str(Path(__file__).resolve().parents[2]))


def cargar_datos(ruta):
    """Lee el CSV limpio y se asegura de que exista la columna 'mes'."""
    df = pd.read_csv(ruta)

    # Si el archivo no trae 'mes', se deriva de una columna de fecha.
    if "mes" not in df.columns:
        for col in ("fecha", "fecha_registro", "fecha_inscripcion"):
            if col in df.columns:
                df["mes"] = pd.to_datetime(df[col], errors="coerce").dt.month
                break
    return df


def guardar(resultado, carpeta, numero):
    """Guarda el resultado de una consulta como registros_consulta_N.csv."""
    if isinstance(resultado, pd.Series):
        resultado = resultado.reset_index()
    ruta = os.path.join(carpeta, f"registros_consulta_{numero}.csv")
    resultado.to_csv(ruta, index=False)


def consulta_1(df, carpeta):
    """Consulta 1: participaciones que ya estan finalizadas."""
    print("\n=== Consulta 1: Participaciones ya finalizadas ===")
    finalizados = df[df["estado"].astype(str).str.upper() == "FINALIZADO"]
    print(finalizados.to_string(index=False))
    guardar(finalizados, carpeta, 1)
    return finalizados


def consulta_2(df, carpeta):
    """Consulta 2: participaciones repetidas (mismo usuario en el mismo reto)."""
    print("\n=== Consulta 2: Participaciones repetidas (mismo usuario, mismo reto) ===")
    repetidos = df[df.duplicated(subset=["id_usuario", "id_reto"], keep=False)]
    print(repetidos.to_string(index=False))
    guardar(repetidos, carpeta, 2)
    return repetidos


def consulta_3(df, carpeta):
    """Consulta 3: cuantas participaciones hay por estado."""
    print("\n=== Consulta 3: Cantidad de participaciones por estado ===")
    conteo = df["estado"].value_counts()
    print(conteo.to_string())
    guardar(conteo, carpeta, 3)
    return conteo


def consulta_4(df, carpeta):
    """Consulta 4 (groupby): los 10 retos con mas participantes."""
    print("\n=== Consulta 4: Los 10 retos con mas participantes ===")
    top_retos = df.groupby("id_reto")["id"].count().nlargest(10)
    print(top_retos.to_string())
    guardar(top_retos, carpeta, 4)
    return top_retos


def consulta_5(df, carpeta):
    """Consulta 5 (groupby): cuantas participaciones hubo cada mes."""
    print("\n=== Consulta 5: Participaciones por mes ===")
    por_mes = df.groupby("mes")["id"].count()
    print(por_mes.to_string())
    guardar(por_mes, carpeta, 5)
    return por_mes


def main():
    """Lee el archivo recibido por consola o localiza registros_limpio.csv y ejecuta las cinco consultas."""
    if len(sys.argv) > 1:
        ruta = sys.argv[1]
    else:
        raiz_proyecto = Path(__file__).resolve().parents[2]
        posibles_rutas = [
            raiz_proyecto / "datos" / "limpios" / "registros_limpio.csv",
            raiz_proyecto / "data" / "limpio" / "registros_limpio.csv",
            Path("datos/limpios/registros_limpio.csv"),
            Path("registros_limpio.csv"),
        ]
        ruta = None
        for r in posibles_rutas:
            if r.exists():
                ruta = str(r)
                break

        if not ruta:
            print("Uso: python notebook/consultas/consultar_registros.py [ruta/a/registros_limpio.csv]")
            sys.exit(1)

    carpeta = os.path.dirname(os.path.abspath(ruta))
    df = cargar_datos(ruta)

    consulta_1(df, carpeta)
    consulta_2(df, carpeta)
    consulta_3(df, carpeta)
    consulta_4(df, carpeta)
    consulta_5(df, carpeta)


if __name__ == "__main__":
    main()
