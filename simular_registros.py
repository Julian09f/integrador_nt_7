'''
Tabla puente: vincula un Usuario con un Reto y deja trazabilidad. Crea el script `src/simular_registros.py`. 

Con la libreria **Faker** genera 800 filas falsas de la tabla `registros`, con las MISMAS columnas que usa Backend II. 
Despues **ensucia los datos a proposito**: nulos, duplicados, espacios sobrantes, mayusculas mezcladas y formatos distintos. 
Esos errores son los que vas a arreglar en la etapa de limpieza, asi que tienen que quedar bien puestos.

Usa `Faker("es_CO")` y fija la semilla con `Faker.seed(42)` y `random.seed(42)` para que el resultado sea SIEMPRE el mismo y tu compañero pueda reproducirlo.
'''
import random
import uuid
import pandas as pd
from faker import Faker

#1. configurar el faker a la region que necesitamos
fake = Faker("es_CO")

#2. fijar la semilla para que los datos sean reproducibles y coherentes
Faker.seed(42)
random.seed(42)

#3. Identifico los datos que necesito simular
#id (texto (UUID))
#fecha_registro (fecha y hora)
#observacion (texto)
#estado (texto)
#id_usuario (texto (UUID))
#id_reto (texto (UUID))

#4  identifico los datos que sea un selector

ESTADOS = ["inscrito", "en proceso", "finalizado"]
IDS_USUARIO = [str(uuid.uuid4()) for _ in range(100)]
IDS_RETO = [str(uuid.uuid4()) for _ in range(20)]

#5 definio mi DATASET
FILAS = 800

#6 Construyo una funcion que generar los N datos pedidos (LIMPIOS)
def generar_datos_limpio(numero_datos = FILAS):
    filas = []
    for _ in range(numero_datos):
        filas.append({
            "id":str(uuid.uuid4()),
            "fecha_registro":fake.date_time_between(start_date="-1y", end_date="now"),
            "observacion":fake.sentence(nb_words=10),
            "estado":random.choice(ESTADOS),
            "id_usuario":random.choice(IDS_USUARIO),
            "id_reto":random.choice(IDS_RETO)
        })
    return filas 

variable=pd.DataFrame(generar_datos_limpio())

#Ensuciar los datos

#1. crear una funcion para definir porcentajes de error
def generar_muestra(datos,porcentaje):
    return datos.sample(frac=porcentaje,
    random_state=random.randint(0,999)).index

#2. Crear una funcion para escribir mal un texto
def escribir_mal(texto):
    variantes=[texto.lower(),f" {texto.title()} ", texto.capitalize()]
    return random.choice(variantes)

#3. Convertir booleanos en textos
def convertir_booleano_texto(valor):
    if valor:
        return random.choice(["SI", "1"])
    return random.choice(["NO", "0"])

#4. Funcion para ensuciar los datos
def ensuciar(datos_df):
    datos_df=datos_df.copy()

    #fecha dos formatos mezclados (2026-03-15 14:30:00 y 15/03/2026 14:30)
    iso=datos_df["fecha_registro"].dt.strftime("%Y-%m-%d %H:%M:%S")
    latino=datos_df["fecha_registro"].dt.strftime("%d/%m/%Y %H:%M")
    datos_df["fecha_registro"]=iso
    filas_elegidas=generar_muestra(datos_df,0.4)
    datos_df.loc[filas_elegidas,"fecha_registro"]=latino.loc[filas_elegidas]
    
    #observacion 20% nulos
    filas_elegidas=generar_muestra(datos_df,0.20)
    datos_df.loc[filas_elegidas,"observacion"]=None

    #Se ensucia `estado`: variantes: 'inscrito', 'EN PROCESO', ' Finalizado '.
    filas_elegidas=generar_muestra(datos_df,0.30)
    datos_df.loc[filas_elegidas,"estado"]=datos_df.loc[filas_elegidas,"estado"].map(escribir_mal)

    #10% con el par id_usuario + id_reto REPETIDO (mismo usuario inscrito dos veces en el mismo reto)
    filas_elegidas=generar_muestra(datos_df,0.10)
    filas_origen=datos_df.drop(index=filas_elegidas).sample(n=len(filas_elegidas), random_state=random.randint(0,999)).index
    datos_df.loc[filas_elegidas,["id_usuario","id_reto"]]=datos_df.loc[filas_origen,["id_usuario","id_reto"]].values

    #5% de las filas repetidas tal cual (duplicados exactos)
    filas_duplicadas=datos_df.loc[generar_muestra(datos_df,0.05)]
    datos_df=pd.concat([datos_df,filas_duplicadas],ignore_index=True)

    return datos_df

#5. Funcion principal para exportacion
def generar_registros(n=800):
    df_limpio = pd.DataFrame(generar_datos_limpio(n))
    df = ensuciar(df_limpio)
    return df

if __name__ == "__main__":
    df = generar_registros(800)
    print(df.shape)
    print(df.head())
    print(df.isna().sum())
