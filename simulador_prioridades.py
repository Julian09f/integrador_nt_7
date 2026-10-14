'''

Define el nivel de atención del reto. Crea el script `src/simular_prioridades.py`. Con la librería Faker genera 200 filas falsas
para la tabla `prioridades`, con las mismas columnas que usa Backend II. Después ensucia los datos a propósito:
- nulos
- duplicados
- espacios sobrantes
- mayúsculas mezcladas
- formatos distintos

Esos errores son los que vas a arreglar en la etapa de limpieza, así que tienen que quedar bien puestos.

Usa `Faker("es_CO")` y fija la semilla con `Faker.seed(42)` y `random.seed(42)` para que el resultado sea siempre el mismo.

OJO: `dias_max_respuesta` NO está en el modelo de Backend II: es una columna EXTRA solo para este ejercicio de análisis.

Criterios de aceptación
El script `src/simular_prioridades.py` existe y corre con `python src/simular_prioridades.py` sin errores.

Al inicio se declaran las constantes: `NIVELES`, `DIAS`.

Se generan 200 filas con estas columnas: id (texto (UUID)), nombre (texto), nivel (entero), dias_max_respuesta (entero).

`id` se genera con `str(uuid.uuid4())`.

`nombre` se genera con `random.choice(list(NIVELES.keys()))`.

`nivel` se genera con `NIVELES[nombre]`.

`dias_max_respuesta` se genera con `DIAS[nivel]`.

La semilla esta fija: `Faker.seed(42)` y `random.seed(42)`, para que el archivo sea reproducible.

Se ensucia `nombre`: variantes: 'ALTA', ' alta ', 'Alta'.

Se ensucia `nivel`: a veces como TEXTO ('3'), a veces la palabra ('tres') y 7% en None.

Se ensucia `dias_max_respuesta`: 5% en None y 3% con un valor absurdo (999).

Solo hay 5 prioridades reales, pero se generan 200 filas: llegan repetidas y mal escritas.

8% de las filas repetidas tal cual (duplicados exactos).

Todo se arma en una funcion `generar_prioridades(n=200)` que devuelve el DataFrame (`return df`), para poder importarla desde el script de exportacion.

El bloque `if __name__ == "__main__":` solo imprime `df.shape`, `df.head()` y `df.isna().sum()` para revisar que los datos quedaron sucios.

'''

import random
import uuid

import pandas as pd
from faker import Faker

# Configuración de semillas para reproducibilidad
Faker.seed(42)
random.seed(42)

# Constantes obligatorias para niveles y días
NIVELES = {
    "Crítica": 1,
    "Alta": 2,
    "Media": 3,
    "Baja": 4,
    "Urgente": 5,
}

DIAS = {
    1: 1,
    2: 3,
    3: 7,
    4: 15,
    5: 2,
}

# OJO: dias_max_respuesta NO está en el modelo de Backend II.
# Es una columna EXTRA solo para este ejercicio de análisis.


def generar_prioridades(n=200):
    """Genera 200 filas con datos sucios para la limpieza posterior."""
    nombres_base = list(NIVELES.keys())
    num_duplicados = int(n * 0.08)
    n_base = n - num_duplicados

    ids = [str(uuid.uuid4()) for _ in range(n_base)]
    nombres = [random.choice(nombres_base) for _ in range(n_base)]
    niveles = [NIVELES[nombre] for nombre in nombres]
    dias_max = [DIAS[nivel] for nivel in niveles]

    df = pd.DataFrame(
        {
            "id": ids,
            "nombre": nombres,
            "nivel": niveles,
            "dias_max_respuesta": dias_max,
        }
    )

    # Ensuciar nombre: variantes 'ALTA', ' alta ', 'Alta'
    def ensuciar_nombre(valor):
        opcion = random.random()
        if opcion < 0.2:
            return valor.upper()
        if opcion < 0.4:
            return f" {valor.lower()} "
        if opcion < 0.6:
            return valor.lower()
        return valor

    df["nombre"] = df["nombre"].apply(ensuciar_nombre)

    # Ensuciar nivel: texto, palabra y None
    mapping_palabras = {1: "uno", 2: "dos", 3: "tres", 4: "cuatro", 5: "cinco"}

    def ensuciar_nivel(valor):
        if pd.isna(valor):
            return valor
        opcion = random.random()
        if opcion < 0.07:
            return None
        if opcion < 0.35:
            return str(valor)
        if opcion < 0.55:
            return mapping_palabras.get(valor, str(valor))
        return valor

    df["nivel"] = df["nivel"].apply(ensuciar_nivel)

    # Ensuciar dias_max_respuesta: None y valor absurdo 999
    def ensuciar_dias(valor):
        opcion = random.random()
        if opcion < 0.05:
            return None
        if opcion < 0.08:
            return 999
        return valor

    df["dias_max_respuesta"] = df["dias_max_respuesta"].apply(ensuciar_dias)

    # 8% de filas duplicadas exactas dentro de las 200 finales
    if num_duplicados > 0:
        idxs = df.sample(n=num_duplicados, random_state=42).index
        df = pd.concat([df, df.loc[idxs].copy()], ignore_index=True)

    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    return df


if __name__ == "__main__":
    df = generar_prioridades(200)
    print(df.shape)
    print(df.head())
    print(df.isna().sum())