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
