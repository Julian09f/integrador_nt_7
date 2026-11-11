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

## Ejecutar todo el pipeline: `main.py`
Orquestador con interfaz web local. Ejecuta uno a uno los `.py` de `notebook/` en este orden (alfabético dentro de cada carpeta):
**1. simulaciones → 2. exportaciones → 3. limpieza → 4. consultas → 5. graficas**.

```
python main.py                 # abre la interfaz en http://127.0.0.1:8765
python main.py --cli           # mismo pipeline en la terminal, con colores
python main.py --cli --detener-en-error
python main.py --port 9000 --no-browser
```

| Archivo | Responsabilidad |
|---|---|
| `main.py` | Descubre los scripts (lista blanca), ejecuta cada uno en un proceso aparte (`MPLBACKEND=Agg`, UTF-8, límite 300 s), detecta los archivos creados o modificados en `datos/` y sirve la API local. Solo biblioteca estándar. |
| `interfaz/index.html` | Interfaz (HTML/CSS/JS sin dependencias externas): KPIs, barra de progreso, línea de 5 fases, filtro por tabla, tarjeta por script con estado y tiempo, panel con pestañas **Salida / Avisos / Archivos** (tablas CSV con vista previa de 100 filas y gráficas PNG ampliables) y galería de gráficas. |

**API local** (`127.0.0.1` únicamente): `GET /api/plan`, `POST /api/ejecutar?id=N` (requiere cabecera `X-Token` de la sesión), `GET /api/preview?ruta=datos/...csv`, `GET /archivo?ruta=datos/...`.
**Seguridad:** no se expone a la red, valida la cabecera `Host` (anti DNS rebinding), token aleatorio por sesión en los POST (anti CSRF), solo ejecuta scripts de la lista blanca (el cliente envía un índice, nunca una ruta), solo sirve archivos dentro de `datos/` con extensiones permitidas, un solo script a la vez y toda salida se pinta con `textContent` (sin inyección HTML).
Resultado esperado: `Resumen: 25 scripts, 0 con error.`

## Flujo de datos de `registros`
Tabla puente usuario-reto. Columnas: `id`, `fecha_registro`, `observacion`, `estado`, `id_usuario`, `id_reto`.

| Paso | Archivo | Responsabilidad |
|---|---|---|
| **1. Simular** | `notebook/simulaciones/simular_registros.py` | Genera 800 filas sintéticas con Faker (`es_CO`, semilla 42). Aplica errores deliberados: fechas mezcladas (ISO y latino), 20% observaciones nulas, errores de escritura en estado, 10% pares usuario+reto repetidos y 5% duplicados exactos. |
| **2. Exportar crudos** | `notebook/exportaciones/exportar_registros.py` | Genera `datos/crudos/registros_crudo.{csv,json,xlsx}`. |
| **3. Limpiar** | `notebook/limpieza/limpiar_registros.py` | Elimina duplicados exactos, estandariza estados (`inscrito`, `en proceso`, `finalizado`), unifica fechas a formato estándar, descarta filas con campos obligatorios vacíos y preserva solo el registro más antiguo por par `(id_usuario, id_reto)`. Genera `datos/limpios/registros_limpio.{csv,json,xlsx}`. |
| **4. Consultar (HU Q01)** | `notebook/consultas/consultar_registros.py` | Ejecuta 5 consultas analíticas con Pandas e imprime resultados, guardando `datos/limpios/registros_consulta_{1..5}.csv`. |
| **5. Graficar (HU G01)** | `notebook/graficas/reportar_registros.py` | Genera 3 gráficas en `datos/reportes/registros_grafica_{1..3}.png` (barras por estado, línea temporal por mes, barras horizontales de top 10 retos) e imprime conclusiones analíticas y justificación de bloqueo HTTP 409 Conflict. |

**Ejecución completa del pipeline:**
```bash
python notebook/exportaciones/exportar_registros.py
python notebook/limpieza/limpiar_registros.py
```
Resultado esperado: `Filas crudas: 840 -> filas limpias: 607`. `observacion` puede quedar vacía (no es obligatoria).

La carpeta `datos/` está en `.gitignore`: no se versiona, cada quien la regenera con los comandos anteriores (el resultado es siempre el mismo por la semilla).

## Flujo de datos de `retos`
El elemento central: la necesidad que publica la empresa. Columnas (iguales a Backend II): `id`, `nombre`, `descripcion`, `fecha_inicio`, `fecha_fin`, `estado`, `id_empresa`, `id_categoria`, `id_prioridad`. Los CSV de retos usan separador `;` y codificación UTF-8 con BOM.

| Paso | Archivo | Responsabilidad |
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
