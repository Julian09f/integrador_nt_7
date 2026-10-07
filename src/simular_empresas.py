'''Organizacion que registra o propone retos. Crea el script `src/simular_empresas.py`. Con la libreria **Faker** genera 300 filas falsas de la tabla `empresas`, con las MISMAS columnas que usa Backend II. Despues **ensucia los datos a proposito**: nulos, duplicados, espacios sobrantes, mayusculas mezcladas y formatos distintos. Esos errores son los que vas a arreglar en la etapa de limpieza, asi que tienen que quedar bien puestos.

Usa `Faker("es_CO")` y fija la semilla con `Faker.seed(42)` y `random.seed(42)` para que el resultado sea SIEMPRE el mismo y tu compañero pueda reproducirlo.
'''
import random
import uuid
import pandas as pd
from faker import Faker

#1. configurar el faker a la region que necesito
fake = Faker("es_CO")

#2. Sembrar semillas para tener coherencia en los datos simulados
Faker.seed(42)
random.seed(42)

#3. Identifico los datos que debo simular
#id (texto (UUID))
#nombre (texto)
#nit (texto)
#sector (texto)
#contacto (texto)
#correo (texto)
#telefono (texto)
#activa (booleano)

#4. Identifico los datos que son un selector
SECTORES = ["Logistica", "Tecnologia", "Salud", "Educacion",
            "Comercio", "Manufactura", "Agroindustria", "Construccion"]

#5. Defino mi DATASET
FILAS = 300


#6. Funcion para generar los N datos pedidos (LIMPIOS)
def generar_datos_limpios(numero_datos=FILAS):
    filas = []
    for _ in range(numero_datos):
        filas.append({
            # uuid4() normal NO respeta random.seed; este uuid v4 sale de random y si es reproducible
            "id": str(uuid.UUID(int=random.getrandbits(128), version=4)),
            "nombre": fake.company(),
            "nit": fake.numerify("#########-#"),
            "sector": random.choice(SECTORES),
            "contacto": fake.name(),
            "correo": fake.company_email(),
            "telefono": fake.numerify("3#########"),
            "activa": random.choice([True, False]),
        })
    return filas


#Ensuciar los datos

#1 Funcion para elegir el porcentaje de filas a ensuciar
def generar_muestra(datos, porcentaje):
    return datos.sample(frac=porcentaje,
                        random_state=random.randint(0, 999)).index


#2 Variantes de escritura de un sector
def variar_sector(texto):
    variantes = [texto.upper(), f" {texto.lower()} ", texto.lower()]
    return random.choice(variantes)


#3 NIT con puntos y guion: 9001234567 -> 900.123.456-7
def nit_con_formato(nit):
    d = nit.replace("-", "")
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9]}"


#4 Telefono en uno de tres formatos mezclados
def formatear_telefono(tel):
    formatos = [
        tel,                                          # 3001234567
        f"{tel[:3]} {tel[3:6]} {tel[6:]}",            # 300 123 4567
        f"+57 {tel[:3]}-{tel[3:6]}-{tel[6:]}",        # +57 300-123-4567
    ]
    return random.choice(formatos)


#5 Booleano a texto
def convertir_booleano_texto(valor):
    if valor:
        return random.choice(["SI", "1"])
    return random.choice(["No", "0"])


#6 Funcion para ensuciar los datos
def ensuciar(datos_df):
    datos_df = datos_df.copy()

    #nit: 3% repetidos entre empresas distintas (se hace ANTES de dar formato,
    #para que el NIT sea realmente el mismo numero)
    filas_elegidas = generar_muestra(datos_df, 0.03)
    for i in filas_elegidas:
        otra = random.choice([j for j in datos_df.index if j != i])
        datos_df.loc[i, "nit"] = datos_df.loc[otra, "nit"]

    #nit: la mitad con puntos y guiones, la otra mitad sin nada
    con_formato = generar_muestra(datos_df, 0.5)
    sin_formato = datos_df.index.difference(con_formato)
    datos_df.loc[con_formato, "nit"] = datos_df.loc[con_formato, "nit"].map(nit_con_formato)
    datos_df.loc[sin_formato, "nit"] = datos_df.loc[sin_formato, "nit"].str.replace("-", "", regex=False)

    #nombre: 10% con espacios sobrantes, 15% en MAYUSCULAS
    filas_elegidas = generar_muestra(datos_df, 0.10)
    datos_df.loc[filas_elegidas, "nombre"] = " " + datos_df.loc[filas_elegidas, "nombre"] + " "

    filas_elegidas = generar_muestra(datos_df, 0.15)
    datos_df.loc[filas_elegidas, "nombre"] = datos_df.loc[filas_elegidas, "nombre"].str.upper()

    #sector: variantes del mismo sector (Logistica, LOGISTICA, ' logistica ')
    filas_elegidas = generar_muestra(datos_df, 0.30)
    datos_df.loc[filas_elegidas, "sector"] = datos_df.loc[filas_elegidas, "sector"].map(variar_sector)

    #contacto: 8% en None
    filas_elegidas = generar_muestra(datos_df, 0.08)
    datos_df.loc[filas_elegidas, "contacto"] = None

    #correo: 6% sin arroba (invalido)
    filas_elegidas = generar_muestra(datos_df, 0.06)
    datos_df.loc[filas_elegidas, "correo"] = datos_df.loc[filas_elegidas, "correo"].str.replace("@", "", regex=False)

    #telefono: tres formatos mezclados
    datos_df["telefono"] = datos_df["telefono"].map(formatear_telefono)

    #activa: a veces llega como texto (SI, No, 1, 0)
    datos_df["activa"] = datos_df["activa"].astype(object)  # necesario para poder mezclar bool y texto
    filas_elegidas = generar_muestra(datos_df, 0.30)
    datos_df.loc[filas_elegidas, "activa"] = datos_df.loc[filas_elegidas, "activa"].map(convertir_booleano_texto)

    #duplicados exactos: 5% de las filas repetidas tal cual
    duplicadas = datos_df.sample(frac=0.05, random_state=random.randint(0, 999))
    datos_df = pd.concat([datos_df, duplicadas], ignore_index=True)

    #mezclo para que los duplicados no queden todos al final
    datos_df = datos_df.sample(frac=1, random_state=42).reset_index(drop=True)

    return datos_df


#7. Funcion principal: devuelve el DataFrame para importarla desde el script de exportacion
def generar_empresas(n=300):
    df = pd.DataFrame(generar_datos_limpios(n))
    df = ensuciar(df)
    return df


if __name__ == "__main__":
    df = generar_empresas()
    print(df.shape)
    print(df.head())
    print(df.isna().sum())