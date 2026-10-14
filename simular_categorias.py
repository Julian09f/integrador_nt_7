import random
import uuid
import pandas as pd
from faker import Faker

#1. configurar el faker a la region que necesito
fake=Faker("es_CO")

#2. Sembrar semillas para tener coherencia en los datos simulados
Faker.seed(42)
random.seed(42)

#3. Identifico los datos que debo simular
#id (texto (UUID))
#nombre (texto)
#descripcion (texto)
#area_responsable (texto)

#4. Identifico los datos que sean un selector
CATEGORIAS=["Logistica","Finanzas","Tecnologia","Marketing","Salud",
            "Educacion","Turismo","Agricultura","Construccion","Comercio"]
AREAS=["Operaciones","Comercial","Tecnica","Administrativa","Talento Humano"]

#version con tilde de los nombres (para las variantes de escritura)
CON_TILDE={"Logistica":"logística","Tecnologia":"tecnología",
           "Educacion":"educación","Construccion":"construcción"}

#5. Defino mi DATASET
FILAS=250

#6. Construyo una funcion para generar los N datos pedidos (LIMPIOS)
def generar_datos_limpios(numero_datos=FILAS):
    filas=[]
    for _ in range(numero_datos):
        filas.append({
            "id":str(uuid.uuid4()),
            "nombre":random.choice(CATEGORIAS),
            "descripcion":fake.sentence(nb_words=8),
            "area_responsable":random.choice(AREAS)
        })
    return pd.DataFrame(filas)

#Ensuciar los datos
#1. crear una funcion para definir porcentajes de error
def generar_muestra(datos,porcentaje):
    return datos.sample(frac=porcentaje,
    random_state=random.randint(0,999)).index

#2. crear una funcion para escribir mal un nombre
#(Logistica, LOGISTICA, ' logistica ', logística)
def escribir_mal(texto):
    variantes=[texto.upper(),
               f" {texto.lower()} ",
               CON_TILDE.get(texto,texto.lower())]
    return random.choice(variantes)

#3. funcion para ensuciar los datos
def ensuciar(datos_df):
    datos_df=datos_df.copy()

    #nombre: 60% llega con variantes de escritura del mismo nombre
    filas_elegidas=generar_muestra(datos_df,0.60)
    datos_df.loc[filas_elegidas,"nombre"]=datos_df.loc[filas_elegidas,"nombre"].map(escribir_mal)

    #descripcion: 15% en None
    filas_elegidas=generar_muestra(datos_df,0.15)
    datos_df.loc[filas_elegidas,"descripcion"]=None

    #area_responsable: 10% en None
    filas_elegidas=generar_muestra(datos_df,0.10)
    datos_df.loc[filas_elegidas,"area_responsable"]=None

    #duplicados exactos: 8% de las filas son copia identica de otra fila
    #(al final, para que la copia incluya el id y la suciedad ya aplicada)
    filas_destino=generar_muestra(datos_df,0.08)
    filas_origen=datos_df.drop(filas_destino).sample(
        n=len(filas_destino),random_state=random.randint(0,999)).index
    datos_df.loc[filas_destino]=datos_df.loc[filas_origen].values

    return datos_df

#7. funcion final: genera limpio + ensucia y devuelve el DataFrame
def generar_categorias(n=FILAS):
    df=ensuciar(generar_datos_limpios(n))
    return df

if __name__=="__main__":
    df=generar_categorias()
    print(df.shape)
    print(df.head())
    print(df.isna().sum())