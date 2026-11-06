import sys
from pathlib import Path

#Agrega la raiz del proyecto al path para poder importar "notebook" al ejecutar este archivo directamente
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
from datetime import datetime
from notebook.simulaciones.simular_retos import ESTADOS

#Recomendaciones generales para limpiar un archivo con pandas

#1 Debería crear variables que le ayuden a python a identificar los valores correctos de mi dataset
NOMBRE_ENTIDAD="retos"
CARPETA_PROYECTO=Path(__file__).resolve().parents[2]
CARPETA_CRUDOS=CARPETA_PROYECTO / "data" / "crudo"
CARPETA_LIMPIOS=CARPETA_PROYECTO / "data" / "limpio"
#La simulacion de retos mezcla dos formatos en fecha_inicio: ISO (60%) y latino (40%)
FORMATOS_FECHA=["%Y-%m-%d", "%d/%m/%Y"]
#Columnas sin las cuales un reto no tiene sentido (descripcion y fecha_fin si pueden quedar vacias)
COLUMNAS_OBLIGATORIAS=["id", "nombre", "fecha_inicio", "estado", "id_empresa", "id_categoria", "id_prioridad"]

def verificar_valor_vacio(valor):
    return pd.isna(valor) or str(valor).strip()==""


def leer_datos_crudos():
    ruta=CARPETA_CRUDOS/f"{NOMBRE_ENTIDAD}_sucio.csv"
    return pd.read_csv(ruta,encoding="utf-8-sig")


def limpiar_texto(texto):
    if verificar_valor_vacio(texto):
        return None
    return str(texto).strip()

def limpiar_estado(estado):
    #'en_curso', 'EN CURSO', ' En Curso ' -> 'EN_CURSO'
    if verificar_valor_vacio(estado):
        return None
    estado=str(estado).strip().upper().replace(" ", "_")
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
    datos_df["fecha_inicio"]=pd.to_datetime(datos_df["fecha_inicio"].map(limpiar_fecha))
    datos_df["fecha_fin"]=pd.to_datetime(datos_df["fecha_fin"].map(limpiar_fecha))

    #3. Se descartan los retos sin datos obligatorios o con valores invalidos
    datos_df=datos_df.dropna(subset=COLUMNAS_OBLIGATORIAS)

    #4. El id es la llave primaria: un solo reto por id
    datos_df=datos_df.drop_duplicates(subset=["id"], keep="first")

    #5. Error logico: fecha_fin anterior a fecha_inicio -> la fecha_fin no es confiable y se deja vacia
    datos_df.loc[datos_df["fecha_fin"]<datos_df["fecha_inicio"], "fecha_fin"]=pd.NaT

    #6. Columna derivada para las consultas (HU Q01); queda vacia si no hay fecha_fin valida
    datos_df["duracion_dias"]=(datos_df["fecha_fin"]-datos_df["fecha_inicio"]).dt.days.astype("Int64")

    return datos_df.reset_index(drop=True)


def exportar_retos_limpios(datos_limpios_df):
    CARPETA_LIMPIOS.mkdir(parents=True, exist_ok=True)
    ruta_csv=CARPETA_LIMPIOS/f"{NOMBRE_ENTIDAD}_limpio.csv"
    ruta_excel=CARPETA_LIMPIOS/f"{NOMBRE_ENTIDAD}_limpio.xlsx"
    #utf-8-sig: Excel abre el CSV con tildes y ñ correctas
    datos_limpios_df.to_csv(ruta_csv,index=False,encoding="utf-8-sig",date_format="%Y-%m-%d")
    datos_limpios_df.to_excel(ruta_excel,index=False,sheet_name=NOMBRE_ENTIDAD,engine="openpyxl")
    return [ruta_csv, ruta_excel]


if __name__ == "__main__":
    datos_crudos_df=leer_datos_crudos()
    datos_limpios_df=limpiar_retos(datos_crudos_df)
    print(f"Filas crudas: {len(datos_crudos_df)} -> filas limpias: {len(datos_limpios_df)}")
    print(datos_limpios_df["estado"].value_counts())
    print(datos_limpios_df.isna().sum())
    for ruta in exportar_retos_limpios(datos_limpios_df):
        print(ruta)
