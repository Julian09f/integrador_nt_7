import sys
from pathlib import Path

#Agrega la raiz del proyecto al path para poder importar "notebook" al ejecutar este archivo directamente
#(boton Play o "python limpiar_retos.py" desde cualquier carpeta)
CARPETA_PROYECTO=Path(__file__).resolve().parents[2]
if str(CARPETA_PROYECTO) not in sys.path:
    sys.path.insert(0, str(CARPETA_PROYECTO))

import pandas as pd
from datetime import datetime
from notebook.simulaciones.simular_retos import ESTADOS
from notebook.exportaciones.exportar_retos import CARPETA_CRUDOS,NOMBRE_ENTIDAD,exportar_retos_limpios

#Recomendaciones generales para limpiar un archivo con pandas

#1 Variables que le ayudan a python a identificar los valores correctos del dataset
#La simulacion de retos mezcla dos formatos en fecha_inicio: ISO (2026-03-02) y latino (02/03/2026)
FORMATOS_FECHA=["%Y-%m-%d", "%d/%m/%Y"]
#Columnas sin las cuales un reto no tiene sentido
#(descripcion y fecha_fin si pueden quedar vacias: un reto puede no tener fecha de cierre definida)
COLUMNAS_OBLIGATORIAS=["id", "nombre", "fecha_inicio", "estado", "id_empresa", "id_categoria", "id_prioridad"]

def verificar_valor_vacio(valor):
    return pd.isna(valor) or str(valor).strip()==""


def leer_datos_crudos():
    #exportar_retos guarda el CSV con separador ";"
    ruta=CARPETA_CRUDOS/f"{NOMBRE_ENTIDAD}_crudo.csv"
    return pd.read_csv(ruta,sep=";",encoding="utf-8-sig")


def limpiar_texto(texto):
    if verificar_valor_vacio(texto):
        return None
    return str(texto).strip()

def limpiar_estado(estado):
    #Corrige variantes como 'en_curso', 'EN CURSO' o ' Cerrado '
    if verificar_valor_vacio(estado):
        return None
    estado=str(estado).strip().upper().replace(" ","_")
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


def limpiar_retos(datos_df):
    datos_df=datos_df.copy()

    #1. Duplicados exactos
    datos_df=datos_df.drop_duplicates()

    #2. Limpieza columna por columna
    for columna in ["id", "nombre", "descripcion", "id_empresa", "id_categoria", "id_prioridad"]:
        datos_df[columna]=datos_df[columna].map(limpiar_texto)
    datos_df["estado"]=datos_df["estado"].map(limpiar_estado)
    for columna in ["fecha_inicio", "fecha_fin"]:
        datos_df[columna]=pd.to_datetime(datos_df[columna].map(limpiar_fecha))

    #3. Error logico: fecha_fin anterior a fecha_inicio. Esa fecha no es confiable,
    #   se deja vacia (igual que los retos sin fecha de cierre) en vez de perder el reto
    fechas_invertidas=datos_df["fecha_fin"]<datos_df["fecha_inicio"]
    datos_df.loc[fechas_invertidas,"fecha_fin"]=pd.NaT

    #4. Se descartan los retos sin datos obligatorios o con valores invalidos
    datos_df=datos_df.dropna(subset=COLUMNAS_OBLIGATORIAS)

    #5. El id es unico: si tras limpiar quedan repetidos se conserva el primero
    datos_df=datos_df.drop_duplicates(subset=["id"], keep="first")

    return datos_df.reset_index(drop=True)


if __name__ == "__main__":
    datos_crudos_df=leer_datos_crudos()
    datos_limpios_df=limpiar_retos(datos_crudos_df)
    print(f"Filas crudas: {len(datos_crudos_df)} -> filas limpias: {len(datos_limpios_df)}")
    print(datos_limpios_df["estado"].value_counts())
    print(datos_limpios_df.isna().sum())
    for ruta in exportar_retos_limpios(datos_limpios_df):
        print(ruta)
