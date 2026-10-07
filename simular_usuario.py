import random
import uuid

from faker import Faker

# 1. Configurar el Faker en la región que necesito
fake = Faker("es_CO")

# 2. Sembrar semilla para mantener datos reproducibles
Faker.seed(42)
random.seed(42)

# 3. Identifico los datos que debo simular
# id: texto (UUID)
# nombre: texto
# correo: texto
# contrasena_hash: texto
# rol: texto
# activo: booleano
# fecha_registro: fecha y hora

# 4. Defino el conjunto de roles
ROLES = ["ADMIN", "EMPRESA", "PARTICIPANTE"]

# 5. Cantidad de filas
FILA = 200


# 6. Genero datos limpios

def generar_datos_limpios(numero_datos=FILA):
    filas = []
    for _ in range(numero_datos):
        filas.append(
            {
                "id": str(uuid.uuid4()),
                "nombre": fake.name(),
                "correo": fake.email(),
                "contrasena_hash": fake.sha256(),
                "rol": random.choice(ROLES),
                "activo": random.choice([True, False]),
                "fecha_registro": fake.date_time_this_decade(),
            }
        )
    return filas


if __name__ == "__main__":
    datos = generar_datos_limpios()
    print(f"Se generaron {len(datos)} registros.")
    print(datos[0])
