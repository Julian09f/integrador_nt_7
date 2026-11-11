#Rutina para convertir una lista de diccionarios en  multiples fuentes de informacion
import sys
from pathlib import Path

#1. Configuracion (cambiar segun su tabla)
NOMBRE_ENTIDAD="retos"
CARPETA_PROYECTO=Path(__file__).resolve().parents[2]

# Agrega la raiz del proyecto al sys.path para que "from notebook..." funcione
# tanto con el boton Play como con "python exportar_retos.py" desde cualquier carpeta
if str(CARPETA_PROYECTO) not in sys.path:
    sys.path.insert(0, str(CARPETA_PROYECTO))
CARPETA_CRUDOS=CARPETA_PROYECTO/"datos"/"crudos"
CARPETA_LIMPIOS=CARPETA_PROYECTO/"datos"/"limpios"
CARPETA_REPORTES=CARPETA_PROYECTO/"datos"/"reportes"

#2. Funciones genericas para elaborar los archivos

#2.1 CREAR LA CARPETA SI NO EXISTE
def preparar_carpeta(carpeta):
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta

#2.2 EXPORTAR A CSV
def exportar_csv(datos_df,carpeta,nombre_archivo):
    ruta=preparar_carpeta(carpeta)/f"{nombre_archivo}.csv"
    datos_df.to_csv(ruta,index=False,sep=";",encoding="utf-8-sig")
    return ruta

#2.3 EXPORTAR A JSON
def exportar_json(datos_df,carpeta,nombre_archivo):
    ruta=preparar_carpeta(carpeta)/f"{nombre_archivo}.json"
    #force_ascii=False permite ver tildes y ñ en el archivo
    datos_df.to_json(ruta,orient="records",date_format="iso",indent=2,force_ascii=False)
    return ruta

#2.4 EXPORTAR A EXCEL
def exportar_excel(datos_df,carpeta,nombre_archivo):
    ruta=preparar_carpeta(carpeta)/f"{nombre_archivo}.xlsx"
    datos_df.to_excel(ruta, index=False, engine="openpyxl")
    return ruta

#3. Genero los archivos en mi proyecto

#Forma minima que pide la HU X01 para la tabla retos (validacion traida de develop)
FILAS_ESPERADAS=500
COLUMNAS_HU=["id", "nombre", "descripcion", "fecha_inicio", "fecha_fin",
             "estado", "id_empresa", "id_categoria", "id_prioridad"]

def validar_retos(datos_df):
    faltan=[columna for columna in COLUMNAS_HU if columna not in datos_df.columns]
    if faltan:
        raise ValueError(f"faltan columnas de la HU: {faltan}")
    if len(datos_df)<FILAS_ESPERADAS:
        raise ValueError(f"se esperaban al menos {FILAS_ESPERADAS} filas, llegaron {len(datos_df)}")

def exportar_retos_crudos(datos_sucios_df):
    validar_retos(datos_sucios_df)
    return [
        exportar_csv(datos_sucios_df,CARPETA_CRUDOS,f"{NOMBRE_ENTIDAD}_crudo"),

        exportar_json(datos_sucios_df,CARPETA_CRUDOS,f"{NOMBRE_ENTIDAD}_crudo"),

        exportar_excel(datos_sucios_df,CARPETA_CRUDOS,f"{NOMBRE_ENTIDAD}_crudo")
    ]

def exportar_retos_limpios(datos_limpios_df):
    return [
        exportar_csv(datos_limpios_df,CARPETA_LIMPIOS,f"{NOMBRE_ENTIDAD}_limpio"),

        exportar_json(datos_limpios_df,CARPETA_LIMPIOS,f"{NOMBRE_ENTIDAD}_limpio"),

        exportar_excel(datos_limpios_df,CARPETA_LIMPIOS,f"{NOMBRE_ENTIDAD}_limpio")
    ]


#4. Punto de entrada: genera los retos simulados (sucios) y los exporta a datos/crudos
if __name__ == "__main__":
    from notebook.simulaciones.simular_retos import generar_retos
    try:
        rutas=exportar_retos_crudos(generar_retos())
    except ValueError as error:
        print(f"ERROR de datos: {error}", file=sys.stderr)
        sys.exit(1)
    except OSError as error:  # permisos, disco lleno, archivo abierto en Excel, etc.
        print(f"ERROR al escribir archivos: {error}", file=sys.stderr)
        sys.exit(2)
    for ruta in rutas:
        print(ruta)
