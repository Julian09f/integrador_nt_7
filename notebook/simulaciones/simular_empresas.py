"""Simula 300 filas de la tabla `empresas` con Faker y las ensucia a proposito.

Las columnas son las MISMAS que usa Backend II:

    id (UUID), nombre, nit, sector, contacto, correo, telefono, activa (bool)

Despues se ensucian los datos (nulos, duplicados, espacios, mayusculas y
formatos distintos). Esos errores son los que arregla la etapa de limpieza.

Uso:
    python notebook/simulaciones/simular_empresas.py
"""

import random
import uuid

import pandas as pd
from faker import Faker

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
SECTORES = [
    "Logistica",
    "Tecnologia",
    "Salud",
    "Educacion",
    "Agricultura",
    "Energia",
    "Finanzas",
    "Turismo",
]

SEMILLA = 42
PORC_NOMBRE_ESPACIOS = 0.10
PORC_NOMBRE_MAYUSCULAS = 0.15
PORC_SECTOR_VARIANTE = 0.40
PORC_CONTACTO_NULO = 0.08
PORC_CORREO_INVALIDO = 0.06
PORC_ACTIVA_TEXTO = 0.20
PORC_DUPLICADOS = 0.05
PORC_NIT_REPETIDO = 0.03


def _uuid_reproducible():
    """UUID v4 que SI respeta la semilla (uuid.uuid4() usa os.urandom y no
    obedece a random.seed(), asi que los id cambiarian en cada corrida)."""
    return str(uuid.UUID(int=random.getrandbits(128), version=4))


def _nit_con_puntos(nit):
    """'900123456-7' -> '900.123.456-7'"""
    cuerpo, dv = nit.split("-")
    return f"{cuerpo[:3]}.{cuerpo[3:6]}.{cuerpo[6:]}-{dv}"


def _telefono_con_formato(tel):
    """Mezcla tres formatos: '3001234567', '300 123 4567', '+57 300-123-4567'."""
    formato = random.choice(["pegado", "espacios", "internacional"])
    if formato == "espacios":
        return f"{tel[:3]} {tel[3:6]} {tel[6:]}"
    if formato == "internacional":
        return f"+57 {tel[:3]}-{tel[3:6]}-{tel[6:]}"
    return tel


def generar_empresas(n=300):
    """Genera `n` filas de `empresas` ya ensuciadas y devuelve el DataFrame."""
    # Semilla fija: el resultado es SIEMPRE el mismo
    Faker.seed(SEMILLA)
    random.seed(SEMILLA)
    fake = Faker("es_CO")

    n_duplicados = round(n * PORC_DUPLICADOS)
    n_base = n - n_duplicados  # el total final (con duplicados) es `n`

    # 1) Datos limpios
    filas = []
    for _ in range(n_base):
        filas.append(
            {
                "id": _uuid_reproducible(),
                "nombre": fake.company(),
                "nit": fake.numerify("#########-#"),
                "sector": random.choice(SECTORES),
                "contacto": fake.name(),
                "correo": fake.company_email(),
                "telefono": fake.numerify("3#########"),
                "activa": random.choice([True, False]),
            }
        )

    # 2) NIT repetido entre empresas DISTINTAS (el NIT deberia ser unico)
    n_nit_rep = round(n * PORC_NIT_REPETIDO)
    for fila in random.sample(filas, n_nit_rep):
        otra = random.choice([f for f in filas if f is not fila])
        fila["nit"] = otra["nit"]

    # 3) Ensuciar por fila
    for fila in filas:
        # nombre: espacios sobrantes (10%) y MAYUSCULAS (15%)
        if random.random() < PORC_NOMBRE_ESPACIOS:
            fila["nombre"] = f"  {fila['nombre']}  "
        if random.random() < PORC_NOMBRE_MAYUSCULAS:
            fila["nombre"] = fila["nombre"].upper()

        # nit: la mitad con puntos y guiones, la otra mitad sin nada
        if random.random() < 0.5:
            fila["nit"] = _nit_con_puntos(fila["nit"])
        else:
            fila["nit"] = fila["nit"].replace("-", "")

        # sector: variantes del mismo sector
        if random.random() < PORC_SECTOR_VARIANTE:
            fila["sector"] = random.choice(
                [fila["sector"].upper(), f" {fila['sector'].lower()} "]
            )

        # contacto: 8% nulos
        if random.random() < PORC_CONTACTO_NULO:
            fila["contacto"] = None

        # correo: 6% sin arroba (invalido)
        if random.random() < PORC_CORREO_INVALIDO:
            fila["correo"] = fila["correo"].replace("@", "")

        # telefono: tres formatos mezclados
        fila["telefono"] = _telefono_con_formato(fila["telefono"])

        # activa: a veces como texto ('SI', 'No', '1', '0')
        if random.random() < PORC_ACTIVA_TEXTO:
            if fila["activa"]:
                fila["activa"] = random.choice(["SI", "1"])
            else:
                fila["activa"] = random.choice(["No", "0"])

    # 4) Duplicados exactos (misma fila repetida tal cual)
    filas += [dict(f) for f in random.sample(filas, n_duplicados)]

    random.shuffle(filas)
    columnas = ["id", "nombre", "nit", "sector", "contacto", "correo", "telefono", "activa"]
    return pd.DataFrame(filas, columns=columnas)


if __name__ == "__main__":
    df = generar_empresas()
    print(df.shape)
    print(df.head())
    print(df.isna().sum())
