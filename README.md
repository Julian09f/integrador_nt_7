# integrador_nt_7
Proyecto integrador de nuevas tecnologias

## Preparar el entorno (una sola vez)
Requisito: Python 3.13. Desde la raíz del proyecto, en PowerShell:
```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Si PowerShell bloquea `Activate.ps1`, ejecutar una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, o no activar el entorno y anteponer `.venv\Scripts\python.exe` a cada comando.
En VS Code: `Ctrl+Shift+P` > *Python: Select Interpreter* > `.venv`. Si el editor marca "Cannot find module matplotlib" (o pandas), falta el paso `pip install -r requirements.txt` en el `.venv`.

## Guía de ejecución completa (sustentación)
Todos los comandos se ejecutan desde la raíz del proyecto con el `.venv` activo. Cada script resuelve sus rutas con `Path(__file__)`, así que también funciona desde otra carpeta.

| # | Comando | Qué demostrar | Resultado esperado |
|---|---|---|---|
| 1 | `python notebook/exportaciones/exportar_retos.py` | Simulación con Faker + datos ensuciados a propósito, exportados en 3 formatos (HU F01 y X01). | `data/crudo/retos_sucio.{csv,xlsx,json}` con shape `(525, 9)`. |
| 2 | `python notebook/limpieza/limpiar_retos.py` | Limpieza: duplicados, espacios, `estado` normalizado, fechas ISO, `duracion_dias`. | `Filas crudas: 525 -> filas limpias: 500`, conteo por estado y nulos por columna. Genera `data/limpio/retos_limpio.{csv,xlsx}`. |
| 3 | `python notebook/consultas/consultar_retos.py` | 5 consultas con pandas, 2 con `groupby` (HU Q01). | 5 bloques `=== Consulta N ===` y `data/limpio/retos_consulta_{1..5}.csv`. |
| 4 | `python notebook/graficas/reportar_retos.py` | 3 gráficas con matplotlib + conclusiones (HU G01). | `reportes/retos_grafica_{1,2,3}.png` (barras por estado, línea por mes, histograma de duración) y 3 conclusiones. |
| 5 | `python notebook/exportaciones/exportar_registros.py` | Simulación y exportación de `registros`. | `datos/crudos/registros_crudo.{csv,json,xlsx}`. |
| 6 | `python notebook/limpieza/limpiar_registros.py` | Limpieza de `registros`. | `Filas crudas: 840 -> filas limpias: 607` y `datos/limpios/registros_limpio.{csv,json,xlsx}`. |

El orden importa: cada paso lee lo que dejó el anterior (1 → 2 → 3 y 4; 5 → 6).
Los `AVISO: 65 fila(s) con duracion_dias vacía` de los pasos 3 y 4 son esperados (ver flujo de `retos`).
El paso 1 cambia `id` y fechas en cada ejecución (`uuid4` y fechas relativas al día), así que el mes pico de la gráfica 2 puede variar; los conteos por estado y los promedios de duración no cambian (semilla 42). Git mostrará `data/crudo/retos_sucio.*` como modificados: no hace falta commitearlos.
Códigos de salida de consultas y gráficas: 0 OK, 1 error de entrada/datos, 2 error al guardar.

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
| 3. Limpiar | `notebook/limpieza/limpiar_retos.py` | Lee `data/crudo/retos_sucio.csv`, quita duplicados exactos, recorta espacios, normaliza `estado` (`ABIERTO`, `EN_CURSO`, `CERRADO`), unifica `fecha_inicio`/`fecha_fin` a ISO, descarta filas sin datos obligatorios, deja un reto por `id`, vacía `fecha_fin` si es anterior a `fecha_inicio` y calcula `duracion_dias = fecha_fin - fecha_inicio`. Genera `data/limpio/retos_limpio.{csv,xlsx}` (CSV en UTF-8 con BOM para Excel). |
| 4. Consultar (HU Q01) | `notebook/consultas/consultar_retos.py` | Lee `data/limpio/retos_limpio.csv` (o la ruta que se pase) y resuelve 5 consultas: en curso, 10 más largos, conteo por estado, `groupby` de duración por estado y `groupby` de inicios por mes. Guarda `data/limpio/retos_consulta_{1..5}.csv` (neutraliza fórmulas tipo `=`, `+`, `-`, `@` contra CSV Injection). Códigos de salida: 0 OK, 1 error de entrada, 2 error de escritura. |
| 5. Graficar (HU G01) | `notebook/graficas/reportar_retos.py` | Lee `data/limpio/retos_limpio.csv` (o la ruta que se pase) y genera con matplotlib (dpi 120): barras de retos por estado, línea de retos que empiezan cada mes (meses sin retos en 0) e histograma de `duracion_dias` (solo duraciones válidas). Guarda `reportes/retos_grafica_{1,2,3}.png` e imprime 3 conclusiones: mes pico, duración promedio por estado y retos con fechas invertidas. Códigos de salida: 0 OK, 1 error de entrada/datos, 2 error al guardar. |

Ejecución (desde la raíz del proyecto):
```
python notebook/exportaciones/exportar_retos.py
python notebook/limpieza/limpiar_retos.py
python notebook/consultas/consultar_retos.py
python notebook/graficas/reportar_retos.py
```
Resultado esperado de la limpieza: `Filas crudas: 525 -> filas limpias: 500` (196 `ABIERTO`, 159 `EN_CURSO`, 145 `CERRADO`). 65 retos quedan sin `fecha_fin`/`duracion_dias` (8% nulos + 5% con fecha invertida); no se eliminan, y las consultas 2 y 4 los excluyen con un `AVISO`. Si se vuelve a exportar, cambian los `id` y las fechas, y con ellas la consulta 5 (ver nota siguiente).
`.gitignore` excluye todos los `*.csv` y `*.xlsx` y la carpeta `reportes/`: `data/limpio/` y las gráficas no se versionan y se regeneran con los comandos anteriores. Excepción: `data/crudo/retos_sucio.{csv,xlsx}` ya estaban en el repo antes de esa regla y siguen versionados (el `.json` también). Nota: `id` usa `uuid.uuid4()` y `fecha_inicio` un rango relativo al día (`-1y`, `+3m`), como pide la HU, así que esas columnas cambian en cada ejecución. Ubicación en `notebook/` por indicación del docente (la HU menciona `src/`).

## Otros archivos del repositorio
Los scripts de la raíz (`simular_empresas.py`, `simular_categorias.py`, `simular_usuario.py`, `simulador_prioridades.py`, `simular_registros.py`) y `src/simular_empresas.py` son simulaciones de otras tablas hechas por otros integrantes. No forman parte de los flujos de `retos` ni de `registros` y ninguno de esos flujos los importa.
