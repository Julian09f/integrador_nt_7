import sys
from pathlib import Path

#Agrega la raiz del proyecto al path para poder importar "notebook" al ejecutar este archivo directamente
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
from datetime import datetime
from notebook.simulaciones.simular_registros import ESTADOS
from notebook.exportaciones.exportar_registros import CARPETA_CRUDOS,NOMBRE_ENTIDAD,exportar_registros_limpios

#Recomendaciones generales para limpiar un archivo con pandas

#1 Debería crear variables que le ayuden a python a identificar los valores correctos de mi dataset
#La simulacion de registros mezcla dos formatos: ISO y latino
FORMATOS_FECHA=["%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M"]
#Columnas sin las cuales un registro no tiene sentido (observacion si puede quedar vacia)
COLUMNAS_OBLIGATORIAS=["id", "fecha_registro", "estado", "id_usuario", "id_reto"]

def verificar_valor_vacio(valor):
    return pd.isna(valor) or str(valor).strip()==""


def leer_datos_crudos():
    ruta=CARPETA_CRUDOS/f"{NOMBRE_ENTIDAD}_crudo.csv"
    return pd.read_csv(ruta,encoding="utf-8-sig")


def limpiar_texto(texto):
    if verificar_valor_vacio(texto):
        return None
    return str(texto).strip()

def limpiar_estado(estado):
    if verificar_valor_vacio(estado):
        return None
    estado=str(estado).strip().lower()
    if estado not in ESTADOS:
        return None
    return estado

def limpiar_fecha(fecha):
    if verificar_valor_vacio(fecha):
        return None
    fecha=str(fecha).strip()
    for formato in FORMATOS_FECHA:
        try:
            return datetime.strptime(fecha,formato)
        except ValueError:
            continue
    return None


def limpiar_registros(datos_df):
    datos_df=datos_df.copy()

    #1. Duplicados exactos
    datos_df=datos_df.drop_duplicates()

    #2. Limpieza columna por columna
    for columna in ["id", "id_usuario", "id_reto", "observacion"]:
        datos_df[columna]=datos_df[columna].map(limpiar_texto)
    datos_df["estado"]=datos_df["estado"].map(limpiar_estado)
    datos_df["fecha_registro"]=pd.to_datetime(datos_df["fecha_registro"].map(limpiar_fecha))

    #3. Se descartan los registros sin datos obligatorios o con valores invalidos
    datos_df=datos_df.dropna(subset=COLUMNAS_OBLIGATORIAS)

    #4. Un usuario solo puede inscribirse una vez en cada reto: se conserva el registro mas antiguo
    datos_df=datos_df.sort_values("fecha_registro")
    datos_df=datos_df.drop_duplicates(subset=["id_usuario", "id_reto"], keep="first")

    return datos_df.reset_index(drop=True)


if __name__ == "__main__":
    datos_crudos_df=leer_datos_crudos()
    datos_limpios_df=limpiar_registros(datos_crudos_df)
    print(f"Filas crudas: {len(datos_crudos_df)} -> filas limpias: {len(datos_limpios_df)}")
    print(datos_limpios_df["estado"].value_counts())
    print(datos_limpios_df.isna().sum())
    for ruta in exportar_registros_limpios(datos_limpios_df):
        print(ruta)
