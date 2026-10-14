#Rutina para convertir una lista de diccionarios en multiples fuentes de inforamcion 

import json
from pathlib import Path # es la ruta del archivo


#1.  Configarcion (Cambiar segun su tabla)
NOMBRE_ENTIDAD="registros"

CARPETA_PROYECTO=Path(__file__).resolve().parents[2] # con el parents me devuelvo un nivel por encima de donde estoy parado

CARPETA_CRUDOS =CARPETA_PROYECTO / "datos" / "crudos"
CARPETA_LIMPIOS=CARPETA_PROYECTO / "datos" / "limpios"
CARPETA_REPORTES=CARPETA_PROYECTO / "datos" / "reportes"

#2 FUNCIONES GENERICAS PARA ELABORAR LOS ARCHIVOS

#2.1 CREAR LA CARPETA SI NO EXISTE.

def preparar_carpeta(carpeta):
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta

# 2.2 EXPORTAR A CSV

def exportar_csv(datos_df,carpeta,nombre_archivo):
     ruta=preparar_carpeta(carpeta)/f"{nombre_archivo}.csv"
     datos_df.to_csv(ruta, index=False,sep=";",encoding="utf-8-sig")
     return ruta

# 2.3 EXPORTAR A JSON

def exportar_json(datos_df,carpeta,nombre_archivo):
    ruta=preparar_carpeta(carpeta)/f"{nombre_archivo}.json"
    datos_df.to_json(ruta,orient="records",date_format="iso",indent=4)
    return ruta

# 2.4 EXPORTAR A EXCEL

def exportar_excel(datos_df,carpeta,nombre_archivo):
    ruta=preparar_carpeta(carpeta)/f"{nombre_archivo}.xlsx"
    datos_df.to_excel(ruta,index=False,engine="openpyxl") #EL openpyxl permite creaer archivos de excel licenciados.
    return ruta

    #3. GENERO LOS ARCHIVOS EN MI PROYECTO 

    def exportar_usuarios_crudos(datos_sucios_df):
        return[
            exportar_csv(datos_sucios_df,CARPETA_CRUDOS,f"{NOMBRE_ENTIDAD}_crudo"),

            exportar_json(datos_sucios_df,CARPETA_CRUDOS,f"{NOMBRE_ENTIDAD}_crudo"),

            exportar_excel(datos_sucios_df,CARPETA_CRUDOS,f"{NOMBRE_ENTIDAD}_crudo")

        ]