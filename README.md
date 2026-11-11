# integrador_nt_7
Proyecto integrador de nuevas tecnologias

## Preparar el entorno (una sola vez)
Requisito: Python 3.13. Desde la raíz del proyecto, en PowerShell:
```
python -m venv .venv
.venv\Scripts\Activate.ps1
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

## Flujo de datos de `retos`
Columnas: `id`, `nombre`, `descripcion`, `fecha_inicio`, `fecha_fin`, `estado`, `id_empresa`, `id_categoria`, `id_prioridad`. CSV con separador `;` y codificación `utf-8-sig`.

| Paso | Archivo | Qué hace |
|---|---|---|
| 1. Simular | `notebook/simulaciones/simular_retos.py` | `generar_retos()` crea 500 filas con Faker (semilla 42, fecha de referencia fija 2026-10-01) y las ensucia: nulos, espacios, `estado` mal escrito, fechas en 2 formatos, fechas invertidas y 5% duplicados exactos. |
| 2. Exportar crudos | `notebook/exportaciones/exportar_retos.py` | Valida columnas y mínimo de 500 filas (HU X01) y genera `datos/crudos/retos_crudo.{csv,json,xlsx}`. Código de salida 1 = error de datos, 2 = error de escritura. |
| 3. Limpiar | `notebook/limpieza/limpiar_retos.py` | Genera `datos/limpios/retos_limpio.{csv,json,xlsx}`. |
| 4. Consultar | `notebook/consultas/consultar_retos.py` | HU Q01: cinco consultas; `duracion_dias` se calcula de las fechas. Salida en `datos/reportes/retos_consulta_N.csv`. |
| 5. Graficar | `notebook/graficas/reportar_retos.py` | HU G01: tres gráficas en `datos/reportes/retos_grafica_N.png` y conclusiones. |

```
python notebook/exportaciones/exportar_retos.py
python notebook/limpieza/limpiar_retos.py
python notebook/consultas/consultar_retos.py
python notebook/graficas/reportar_retos.py
```

La carpeta `datos/` está en `.gitignore`: no se versiona, cada quien la regenera con los comandos anteriores (el resultado es siempre el mismo por la semilla).
