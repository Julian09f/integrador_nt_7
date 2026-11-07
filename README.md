# integrador_nt_7
Proyecto integrador de nuevas tecnologias

## Preparar el entorno
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
En VS Code: `Ctrl+Shift+P` → **Python: Select Interpreter** → `.\.venv\Scripts\python.exe`, para que el botón ▶ use este entorno. Si un script falla con `ModuleNotFoundError: No module named 'pandas'` (o `matplotlib`), el entorno no tiene las dependencias: repetir `pip install -r requirements.txt` con el `.venv` activado.

Todos los scripts de `notebook/` agregan la raíz del proyecto al `sys.path`, así que funcionan con el botón ▶, con `python <archivo>.py` desde su propia carpeta o con la ruta completa desde cualquier carpeta.

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
El elemento central: la necesidad que publica la empresa. Columnas (iguales a Backend II): `id`, `nombre`, `descripcion`, `fecha_inicio`, `fecha_fin`, `estado`, `id_empresa`, `id_categoria`, `id_prioridad`. Los CSV de retos usan separador `;` y codificación UTF-8 con BOM.

| Paso | Archivo | Qué hace |
|---|---|---|
| 1. Simular | `notebook/simulaciones/simular_retos.py` | `generar_retos()` crea 500 filas con Faker (`es_CO`, semilla 42, fecha de referencia 2026-10-01) y las ensucia: 10% `nombre` con espacios, 12% `descripcion` nula, 5% `fecha_fin` anterior a `fecha_inicio`, 8% `fecha_fin` nula, `fecha_inicio` en 2 formatos (ISO y `dd/mm/aaaa`), 7% `estado` mal escrito, 5% duplicados exactos. |
| 2. Exportar crudos | `notebook/exportaciones/exportar_retos.py` | Genera `datos/crudos/retos_crudo.{csv,json,xlsx}`. Expone `exportar_retos_crudos()` y `exportar_retos_limpios()`. |
| 3. Limpiar | `notebook/limpieza/limpiar_retos.py` | Quita duplicados exactos, recorta textos, normaliza `estado` (`ABIERTO`, `EN_CURSO`, `CERRADO`), unifica fechas, deja vacía la `fecha_fin` anterior a `fecha_inicio` (se conserva el reto), descarta filas sin datos obligatorios y deja un `id` único. Genera `datos/limpios/retos_limpio.{csv,json,xlsx}`. |
| 4. Consultar (HU Q01) | `notebook/consultas/consultar_retos.py` | 5 consultas (2 con `groupby`) sobre el CSV limpio. Guarda `datos/reportes/retos_consulta_{1..5}.csv`. |
| 5. Graficar (HU G01) | `notebook/graficas/reportar_retos.py` | 3 gráficas con matplotlib (barras por estado, línea por mes, histograma de duración) y conclusiones. Guarda `datos/reportes/retos_grafica_{1..3}.png`. |

`duracion_dias` no es columna de la tabla: los pasos 4 y 5 la calculan como `fecha_fin - fecha_inicio`; queda vacía en los retos sin `fecha_fin` (se excluyen de promedios e histograma).

Ejecución en orden (desde la raíz del proyecto, con el `.venv` activado):
```
python notebook/exportaciones/exportar_retos.py
python notebook/limpieza/limpiar_retos.py
python notebook/consultas/consultar_retos.py
python notebook/graficas/reportar_retos.py
```
Resultado esperado: `Filas crudas: 525 -> filas limpias: 500` (ABIERTO 196, EN_CURSO 159, CERRADO 145; 60 `descripcion` vacías y 65 `fecha_fin` vacías, que es lo esperado). Las consultas y gráficas avisan por consola de los 65 retos sin `fecha_fin`; es informativo, no un error.
