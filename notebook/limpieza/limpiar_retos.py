import sys
from pathlib import Path

#Agrega la raiz del proyecto al path para poder importar "notebook" al ejecutar este archivo directamente
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd
from datetime import datetime
from notebook.simulaciones.simular_registros import CARPETA_CRUDOS,NOMBRE_ENTIDAD

#Recomendaciones generales para limpiar un archivo con pandas

#1 Debería crear variables que le ayuden a python a identificar los valroes correctos de mi dataset
ROLES=["ADMIN", "EMPRESA", "PARTICIPANTE"]
#La simulacion de registros mezcla dos formatos: ISO y latino
FORMATOS_FECHA=["%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M"]

def verificar_valor_vacio(valor):
    return pd.isna(valor) or str(valor).strip()==""


def leer_datos_crudos():
    ruta=CARPETA_CRUDOS/f"{NOMBRE_ENTIDAD}_crudo.csv"
    return pd.read_csv(ruta)


def limpiar_nombre(nombre):
    if verificar_valor_vacio(nombre):
        return None
    nombre=nombre.strip()
    return nombre.title()

def limpiar_correo(correo):
    if verificar_valor_vacio(correo):
        return None
    correo=correo.strip().lower()
    if "@" not in correo:
        return None
    return correo

def limpiar_rol(rol):
    if verificar_valor_vacio(rol):
        return None
    rol=rol.strip().upper()
    if rol not in ROLES:
        return None
    return rol

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
