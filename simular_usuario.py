import random
from datetime import datetime, timedelta
import pandas as pd
from faker import Faker

#1. configurar el faker a la region que necesito
fake=Faker("es_CO")

#2. Sembrar semillas para tener coherencia en los datos
#simulados
Faker.seed(42)
random.seed(42)

#3. Identifico los datos que debo simular
#id (texto (UUID))
#nombre (texto)
#correo (texto)
#contrasena_hash (texto)
#rol (texto)
#activo (booleano),
#fecha_registro (fecha y hora)

#4. Identifico los datos o el dato que sea un selector
ROLES=["ADMIN","EMPRESA","PARTICIPANTE"]

#5. Defino mi DATASET
FILAS=400

# Fecha fija de referencia: si se usa "now" los datos cambian con cada ejecucion
FECHA_REFERENCIA=datetime(2026, 10, 1)

#6. Construyo una funcion para generar los N datos pedidos (LIMPIOS)
# Se usa fake.uuid4() (y no uuid.uuid4()) porque respeta la semilla.
def generar_datos_limpios(numero_datos=FILAS):
    filas=[]
    for _ in range(numero_datos):

        filas.append({
            "id":fake.uuid4(),
            "nombre":fake.name(),
            "correo":fake.email(),
            "contrasena_hash":fake.sha256(),
            "rol":random.choice(ROLES),
            "activo":random.choice([True,False]),
            "fecha_registro":fake.date_time_between(start_date=FECHA_REFERENCIA-timedelta(days=730), end_date=FECHA_REFERENCIA)

        })
    return filas

#Ensuciar los datos

#1. Crear una funcion para definir procentajes de error
def generar_muestra(datos,porcentaje):
    return datos.sample(frac=porcentaje, random_state=random.randint(0,999)).index

#2. Crear una funcion para escribir mal un texto
def escribir_mal(texto):
    variantes=[texto.lower(),f" {texto.title()} ", texto.capitalize()]
    return random.choice(variantes)

#3. Convertir boolenos en textos
def convertir_booleano_texto(valor):
    if valor:
        return random.choice(["SI", "1"])
    return random.choice(["NO", "0"])

#4. Funcion para ensuciar los datos
def ensuciar(datos_df):
    datos_df=datos_df.copy()
    #nombre: 10% con espacios sobrantes, 8% Mayuscula
    filas_elegidas=generar_muestra(datos_df,0.10)
    datos_df.loc[filas_elegidas,"nombre"]=" "+datos_df.loc[filas_elegidas,"nombre"]+" "

    filas_elegidas=generar_muestra(datos_df,0.08)
    datos_df.loc[filas_elegidas,"nombre"]=datos_df.loc[filas_elegidas,"nombre"].str.upper()

    #correo: 12% Mayusculas 5% sin el arroba 4% en None
    filas_elegidas=generar_muestra(datos_df,0.12)
    datos_df.loc[filas_elegidas,"correo"]=datos_df.loc[filas_elegidas,"correo"].str.upper()

    filas_elegidas=generar_muestra(datos_df,0.05)
    datos_df.loc[filas_elegidas,"correo"]=datos_df.loc[filas_elegidas,"correo"].str.replace("@","", regex=False)

    filas_elegidas=generar_muestra(datos_df,0.04)
    datos_df.loc[filas_elegidas,"correo"]=None

    #rol variantes de escritura (admin ADMIN Admin)
    filas_elegidas=generar_muestra(datos_df,0.07)
    datos_df.loc[filas_elegidas,"rol"]=datos_df.loc[filas_elegidas,"rol"].map(escribir_mal)

    #fecha dos formatos mezclados (2026-03-15 14:30:00 y 15/03/2026 14:30)
    iso=datos_df["fecha_registro"].dt.strftime("%Y-%m-%d %H:%M:%S")
    latino=datos_df["fecha_registro"].dt.strftime("%d/%m/%Y %H:%M")
    datos_df["fecha_registro"]=iso
    filas_elegidas=generar_muestra(datos_df,0.4)
    datos_df.loc[filas_elegidas,"fecha_registro"]=latino.loc[filas_elegidas]

    #activo en ocaciones llega SI NO 1 o 0
    # la columna se pasa a object porque una columna booleana no acepta textos
    datos_df["activo"]=datos_df["activo"].astype(object)
    filas_elegidas=generar_muestra(datos_df,0.3)
    datos_df.loc[filas_elegidas,"activo"]=datos_df.loc[filas_elegidas,"activo"].map(convertir_booleano_texto)

    return datos_df

#5. Funcion principal: genera los usuarios limpios, los ensucia y devuelve el DataFrame
# Se vuelve a fijar la semilla para que cada llamada devuelva SIEMPRE el mismo resultado.
def generar_usuarios(n=FILAS):
    Faker.seed(42)
    random.seed(42)
    df=pd.DataFrame(generar_datos_limpios(n))
    df=ensuciar(df)
    return df


if __name__ == "__main__":
    df=generar_usuarios()
    print(df.shape)
    print(df.head())
    print(df.isna().sum())
