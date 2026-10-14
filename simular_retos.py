''' El elemento central: la necesidad que publica la empresa. Crea el script `src/simular_retos.py`. Con la libreria **Faker** genera 500 filas falsas de la tabla `retos`, con las MISMAS columnas que usa Backend II. Despues **ensucia los datos a proposito**: nulos, duplicados, espacios sobrantes, mayusculas mezcladas y formatos distintos. Esos errores son los que vas a arreglar en la etapa de limpieza, asi que tienen que quedar bien puestos.

Usa `Faker("es_CO")` y fija la semilla con `Faker.seed(42)` y `random.seed(42)` para que el resultado sea SIEMPRE el mismo y tu compañero pueda reproducirlo.'''


import random
from datetime import date, timedelta

import pandas as pd
from faker import Faker

#1. configurar el faker a la region que necesito
fake = Faker("es_CO")

#2. Sembrar semillas para tener coherencia en los datos simulados
Faker.seed(42)
random.seed(42)

'''identifico los datos que necesito simular
id (texto uuid)
nombre (texto)
descripcion (texto)
fecha_inicio (fecha)
fecha_fin (fecha)
estado (texto)
id_empresa (texto uuid)
id_categoria (texto uuid)
id_prioridad (texto uuid)
'''

#3. Identifico los datos que sean un selector
# OJO: verificar estos valores contra el enum de estado que usa Backend II
ESTADOS = ["ABIERTO", "EN_CURSO", "CERRADO"]

# Las llaves foraneas deben repetirse entre retos (varios retos por empresa),
# por eso se genera un catalogo pequeño de ids y se elige de ahi.
# Se usa un Faker aparte con su propia semilla para que estos ids no salgan
# de la misma secuencia aleatoria que los ids de los retos.
fake_ids = Faker()
fake_ids.seed_instance(7)
IDS_EMPRESA = [fake_ids.uuid4() for _ in range(40)]
IDS_CATEGORIA = [fake_ids.uuid4() for _ in range(8)]
IDS_PRIORIDAD = [fake_ids.uuid4() for _ in range(3)]

#4. Defino mi DATASET
FILAS = 500

# Fecha fija de referencia: si se usa "-1y" o "+3m" los datos cambian segun el dia de ejecucion
FECHA_REFERENCIA = date(2026, 10, 1)

#5. Construyo una funcion para generar los N datos pedidos (LIMPIOS)
def generar_datos_limpios(numero_datos=FILAS):
    filas = []
    for _ in range(numero_datos):
        fecha_inicio = fake.date_between(start_date=FECHA_REFERENCIA - timedelta(days=365),
                                         end_date=FECHA_REFERENCIA + timedelta(days=90))
        filas.append({
            "id": fake.uuid4(),
            "nombre": fake.sentence(nb_words=6).rstrip("."),
            "descripcion": fake.sentence(nb_words=12),
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_inicio + timedelta(days=random.randint(15, 180)),
            "estado": random.choice(ESTADOS),
            "id_empresa": random.choice(IDS_EMPRESA),
            "id_categoria": random.choice(IDS_CATEGORIA),
            "id_prioridad": random.choice(IDS_PRIORIDAD),
        })
    return filas

#Ensuciar los datos

#1. Crear una funcion para definir porcentajes de error (procesos estocasticos)
def generar_muestra(datos, porcentaje):
    return datos.sample(frac=porcentaje, random_state=random.randint(0, 999)).index

#2. Crear una funcion para escribir mal un texto ('en_curso', 'EN CURSO', ' Cerrado ')
def escribir_mal(texto):
    variantes = [
        texto.lower(),
        texto.replace("_", " "),
        f" {texto.replace('_', ' ').title()} ",
    ]
    return random.choice(variantes)

#3. Funcion para ensuciar los datos
def ensuciar(datos_df):
    datos_df = datos_df.copy()

    #nombre: 10% con espacios sobrantes
    filas_elegidas = generar_muestra(datos_df, 0.10)
    datos_df.loc[filas_elegidas, "nombre"] = " " + datos_df.loc[filas_elegidas, "nombre"] + " "

    #descripcion: 12% en None (nulos)
    filas_elegidas = generar_muestra(datos_df, 0.12)
    datos_df.loc[filas_elegidas, "descripcion"] = None

    #fecha_fin: 5% ANTERIOR a fecha_inicio (error logico a detectar)
    # se hace antes de convertir fecha_inicio a texto, porque se necesita la fecha real
    filas_invertidas = generar_muestra(datos_df, 0.05)
    datos_df.loc[filas_invertidas, "fecha_fin"] = [
        inicio - timedelta(days=random.randint(1, 30))
        for inicio in datos_df.loc[filas_invertidas, "fecha_inicio"]
    ]

    #fecha_fin: 8% en None (se eligen entre las filas no invertidas para no pisar el error anterior)
    restantes = datos_df.drop(index=filas_invertidas)
    filas_elegidas = restantes.sample(n=round(len(datos_df) * 0.08),
    random_state=random.randint(0, 999)).index
    datos_df.loc[filas_elegidas, "fecha_fin"] = None

    #fecha_inicio: dos formatos mezclados "2026-03-02" (60%) y "02/03/2026" (40%)
    fechas = pd.to_datetime(datos_df["fecha_inicio"])
    iso = fechas.dt.strftime("%Y-%m-%d")
    latino = fechas.dt.strftime("%d/%m/%Y")
    datos_df["fecha_inicio"] = iso
    filas_elegidas = generar_muestra(datos_df, 0.4)
    datos_df.loc[filas_elegidas, "fecha_inicio"] = latino.loc[filas_elegidas]

    #estado: 7% con variantes de escritura ('en_curso', 'EN CURSO', ' Cerrado ')
    filas_elegidas = generar_muestra(datos_df, 0.07)
    datos_df.loc[filas_elegidas, "estado"] = datos_df.loc[filas_elegidas, "estado"].map(escribir_mal)

    #5% de las filas repetidas tal cual (duplicados exactos)
    datos_duplicados = datos_df.sample(frac=0.05, random_state=22)
    datos_df = pd.concat([datos_df, datos_duplicados], ignore_index=True)

    return datos_df


#4. Funcion principal: genera los retos limpios, los ensucia y devuelve el DataFrame
# Se vuelve a fijar la semilla para que cada llamada (por ejemplo desde el script
# de exportacion) devuelva SIEMPRE el mismo resultado.
def generar_retos(n=FILAS):
    Faker.seed(42)
    random.seed(42)
    df = pd.DataFrame(generar_datos_limpios(n))
    df = ensuciar(df)
    return df


if __name__ == "__main__":
    df = generar_retos()
    print(df.shape)
    print(df.head())
    print(df.isna().sum())
