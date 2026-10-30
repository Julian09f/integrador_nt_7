# integrador_nt_7
Proyecto integrador de nuevas tecnologias

## Preparar el entorno
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Flujo de datos de `registros`
Tabla puente usuario-reto. Columnas: `id`, `fecha_registro`, `observacion`, `estado`, `id_usuario`, `id_reto`.

| Paso | Archivo | Qué hace |
|---|---|---|
| 1. Simular | `notebook/simulaciones/simular_registros.py` | `generar_registros()` crea 800 filas con Faker (semilla 42, fechas fijas en 2025) y las ensucia: fechas en 2 formatos, 20% `observacion` nula, `estado` mal escrito, 10% pares usuario+reto repetidos, 5% duplicados exactos. |
| 2. Exportar crudos | `notebook/exportaciones/exportar_registros.py` | Ejecutarlo genera `datos/crudos/registros_crudo.{csv,json,xlsx}`. |
| 3. Limpiar | `notebook/limpieza/limpiar_registros.py` | Lee el CSV crudo, quita duplicados exactos, normaliza texto y `estado` (`inscrito`, `en proceso`, `finalizado`), unifica fechas, descarta filas sin datos obligatorios y deja un solo registro por par `id_usuario`+`id_reto` (el más antiguo). Genera `datos/limpios/registros_limpio.{csv,json,xlsx}`. |

Ejecución (desde la raiz del proyecto):
```
python notebook/exportaciones/exportar_registros.py
python notebook/limpieza/limpiar_registros.py
```
Resultado esperado: `Filas crudas: 840 -> filas limpias: 607`. `observacion` puede quedar vacía (no es obligatoria).

La carpeta `datos/` está en `.gitignore`: no se versiona, cada quien la regenera con los comandos anteriores (el resultado es siempre el mismo por la semilla).


## Flujo de datos de `retos`
Columnas: `id`, `nombre`, `descripcion`, `fecha_inicio`, `fecha_fin`, `estado`, `id_empresa`, `id_categoria`, `id_prioridad`.

| Paso | Archivo | Qué hace |
|---|---|---|
| 1. Simular (HU F01) | `notebook/simulaciones/simular_retos.py` | `generar_retos(n=500)` crea 500 filas con Faker (`es_CO`, semilla 42) y las ensucia: 10% `nombre` con espacios, 12% `descripcion` nula, `fecha_inicio` en 2 formatos, 8% `fecha_fin` nula y 5% anterior a `fecha_inicio`, `estado` mal escrito, 5% duplicados exactos (525 filas). |
| 2. Exportar (HU X01) | `notebook/exportaciones/exportar_retos.py` | Importa `generar_retos()` y genera `data/crudo/retos_sucio.{csv,xlsx,json}`. |

Ejecución (desde la raíz del proyecto):
```
python notebook/exportaciones/exportar_retos.py
```
`data/crudo/` sí se versiona. Nota: `id` usa `uuid.uuid4()` y `fecha_inicio` un rango relativo al día (`-1y`, `+3m`), como pide la HU, así que esas columnas cambian en cada ejecución. Ubicación en `notebook/` por indicación del docente (la HU menciona `src/`).