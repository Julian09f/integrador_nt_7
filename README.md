# integrador_nt_7
**Proyecto Integrador de Nuevas Tecnologías**

Este repositorio contiene el pipeline completo de ingeniería, limpieza, consulta analítica y visualización de datos para las entidades del sistema (inspiradas en el modelo relacional de Backend II).

El flujo de trabajo abarca cinco etapas principales:
1. **Simulación de datos sintéticos** con errores deliberados (Faker con semilla reproducible).
2. **Exportación multiformato** a CSV, JSON y Excel en `datos/crudos/`.
3. **Limpieza y normalización** con Pandas hacia `datos/limpios/`.
4. **Consultas analíticas de negocio (HU Q01)** guardadas en `datos/reportes/`.
5. **Reportes visuales con Matplotlib (HU G01)** con 3 gráficas por entidad y conclusiones para el backend.

---

## 📁 Estructura del Proyecto

```text
integrador_nt_7/
├── .gitignore
├── README.md
├── requirements.txt
├── simulador_prioridades.py
├── simular_categorias.py
├── simular_empresas.py
├── simular_registros.py
├── simular_usuario.py
├── src/
│   ├── requirements.txt
│   └── simular_empresas.py
├── datos/                                 # Carpeta generada automáticamente (ignorada en git)
│   ├── crudos/                           # Archivos simulados con datos sucios (*.csv, *.json, *.xlsx)
│   ├── limpios/                          # Archivos procesados y normalizados (*.csv, *.json, *.xlsx)
│   └── reportes/                         # Salida de consultas (*.csv) y gráficas (*.png)
└── notebook/
    ├── simulaciones/                     # Generación de datos sintéticos con Faker
    │   ├── simular_prioridades.py
    │   ├── simular_registros.py
    │   └── simular_retos.py
    ├── exportaciones/                    # Rutinas de exportación a CSV, JSON y Excel
    │   ├── exportar_prioridades.py
    │   ├── exportar_registros.py
    │   └── exportar_retos.py
    ├── limpieza/                         # Pipelines de depuración y normalización
    │   ├── limpiar_prioridades.py
    │   ├── limpiar_registros.py
    │   └── limpiar_retos.py
    ├── consultas/                        # Historias de usuario HU Q01 (consultas analíticas)
    │   ├── consultar_prioridades.py
    │   ├── consultar_registros.py
    │   └── consultar_retos.py
    └── graficas/                         # Historias de usuario HU G01 (gráficas con Matplotlib)
        ├── reportar_prioridades.py
        ├── reportar_registros.py
        └── reportar_retos.py
```

---

## ⚙️ Preparación del Entorno

1. **Crear y activar el entorno virtual:**
   ```bash
   # En Windows:
   python -m venv .venv
   .venv\Scripts\activate

   # En Linux / macOS:
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuración en VS Code:**
   - Presiona `Ctrl+Shift+P` → **Python: Select Interpreter** → Selecciona `.\.venv\Scripts\python.exe`.
   - Con esto, tanto la terminal integrada como el botón de ejecución ▶ (**Play**) utilizarán el entorno virtual configurado con todas las librerías instaladas (`pandas`, `matplotlib`, `faker`, `openpyxl`).

---

## 🏛️ Arquitectura y Principios de los Scripts

Todos los scripts dentro de `notebook/` fueron diseñados bajo los siguientes principios de ingeniería:

* **Independencia del directorio de ejecución:** Usan `Path(__file__).resolve().parents[...]` para calcular dinámicamente la raíz del proyecto. Funcionan igual al ejecutarse desde la raíz, desde su propia subcarpeta o mediante el botón ▶ (**Play**) de VS Code.
* **Flexibilidad en línea de comandos:** Aceptan rutas personalizadas como argumento opcional y, si no se especifican, resuelven automáticamente los archivos por defecto en `datos/limpios/` o `datos/crudos/`.
* **Backend de Matplotlib sin interfaz gráfica (`matplotlib.use("Agg")`):** Permite renderizar y guardar figuras (`.png`) directamente a disco sin abrir ventanas emergentes ni bloquear la consola.
* **Compatibilidad de codificación en Windows:** Configuran la salida estándar a UTF-8 (`sys.stdout.reconfigure(encoding="utf-8")`) para garantizar la correcta visualización de caracteres en español (tildes, ñ).
* **Códigos de salida estandarizados:** Devuelven `0` en ejecuciones exitosas, `1` en errores de datos/validación y `2` en fallos de escritura en disco.

---

## 🔄 Flujos de Datos por Entidad (Pipelines E2E)

### 1. Entidad `registros` (Tabla puente Usuario - Reto)
Vincula usuarios con retos y almacena trazabilidad de participación.
* **Columnas:** `id`, `fecha_registro`, `observacion`, `estado`, `id_usuario`, `id_reto`.
* **Formato:** CSV delimitado por comas `,`, codificación `utf-8-sig`.

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
python notebook/consultas/consultar_registros.py
python notebook/graficas/reportar_registros.py
```
*Resultado esperado:* `840 filas crudas -> 607 filas limpias`.

---

### 2. Entidad `retos` (Necesidades publicadas por empresas)
Representa los retos y desafíos empresariales disponibles en la plataforma.
* **Columnas:** `id`, `nombre`, `descripcion`, `fecha_inicio`, `fecha_fin`, `estado`, `id_empresa`, `id_categoria`, `id_prioridad`.
* **Formato:** CSV delimitado por punto y coma `;`, codificación `utf-8-sig` (con BOM).

| Paso | Archivo | Responsabilidad |
|---|---|---|
| **1. Simular** | `notebook/simulaciones/simular_retos.py` | Genera 500 filas sintéticas con Faker (`es_CO`, semilla 42). Aplica suciedad: espacios sobrantes, 12% descripciones nulas, 5% fechas fin anteriores a fecha inicio (fechas invertidas), 8% sin fecha de fin, estados con variaciones de mayúsculas/espacios y duplicados. |
| **2. Exportar crudos** | `notebook/exportaciones/exportar_retos.py` | Genera `datos/crudos/retos_crudo.{csv,json,xlsx}`. |
| **3. Limpiar** | `notebook/limpieza/limpiar_retos.py` | Elimina duplicados exactos, limpia textos, valida y estandariza estados (`ABIERTO`, `EN_CURSO`, `CERRADO`), normaliza fechas y anula `fecha_fin` en casos donde sea menor a `fecha_inicio` para no descartar el reto. Genera `datos/limpios/retos_limpio.{csv,json,xlsx}`. |
| **4. Consultar (HU Q01)** | `notebook/consultas/consultar_retos.py` | Resuelve 5 consultas analíticas (incluyendo filtros y agrupaciones) y guarda los resultados en `datos/reportes/retos_consulta_{1..5}.csv`. |
| **5. Graficar (HU G01)** | `notebook/graficas/reportar_retos.py` | Genera `datos/reportes/retos_grafica_{1..3}.png` (barras por estado, línea por mes de inicio, histograma de duración en días) e imprime conclusiones para el negocio y el backend. |

**Ejecución completa del pipeline:**
```bash
python notebook/exportaciones/exportar_retos.py
python notebook/limpieza/limpiar_retos.py
python notebook/consultas/consultar_retos.py
python notebook/graficas/reportar_retos.py
```
*Resultado esperado:* `525 filas crudas -> 500 filas limpias`.

---

### 3. Entidad `prioridades` (Nivel de atención y respuesta)
Define la urgencia y tiempos máximos de respuesta de los retos.
* **Columnas:** `id`, `nombre` (o `prioridad`), `nivel`, `dias_max_respuesta`.
* **Formato:** CSV delimitado por comas `,`, codificación `utf-8-sig`.

| Paso | Archivo | Responsabilidad |
|---|---|---|
| **1. Simular** | `notebook/simulaciones/simular_prioridades.py` | Genera 200 filas con los 5 niveles de prioridad. Ensucia nombres (`ALTA`, ` alta `), niveles (números como texto o palabras) y días de respuesta (valores nulos y absurdos como 999). |
| **2. Exportar crudos** | `notebook/exportaciones/exportar_prioridades.py` | Exporta los datos crudos a `datos/crudos/prioridades_crudo.{csv,json,xlsx}`. |
| **3. Limpiar** | `notebook/limpieza/limpiar_prioridades.py` | Normaliza nombres a formato Capitalizado, mapea niveles textuales a enteros (1 a 5), corrige o imputa tiempos de respuesta válidos y elimina duplicados. Genera `datos/limpios/prioridades_limpio_q01.csv`. |
| **4. Consultar (HU Q01)** | `notebook/consultas/consultar_prioridades.py` | Realiza consultas analíticas sobre distribución de prioridades, estados y responsables, exportando reportes. |
| **5. Graficar (HU G01)** | `notebook/graficas/reportar_prioridades.py` | Genera gráficas de distribución de prioridades, estado por prioridad y evolución temporal mensual en `datos/reportes/`. |

**Ejecución completa del pipeline:**
```bash
python notebook/exportaciones/exportar_prioridades.py
python notebook/limpieza/limpiar_prioridades.py
python notebook/consultas/consultar_prioridades.py
python notebook/graficas/reportar_prioridades.py
```

---

## 📂 Descripción Detallada de Subcarpetas en `notebook/`

### 1. `notebook/simulaciones/`
Contiene la lógica de generación sintética de datos.
* Utiliza la librería **Faker** configurada en localización colombiana (`Faker("es_CO")`).
* Fija las semillas aleatorias (`Faker.seed(42)` y `random.seed(42)`) para garantizar **100% de reproducibilidad**.
* Introduce patrones deliberados de suciedad: valores nulos, espacios en blanco accidentales, inconsistencias de mayúsculas/minúsculas, formatos heterogéneos de fechas y registros duplicados.

### 2. `notebook/exportaciones/`
Centraliza la conversión de estructuras en memoria (listas de diccionarios o DataFrames de Pandas) hacia almacenamiento persistente.
* Crea automáticamente las carpetas de destino si no existen (`mkdir(parents=True, exist_ok=True)`).
* Exporta simultáneamente en tres formatos estándar de la industria:
  * **CSV (`.csv`):** Formato plano óptimo para ingesta rápida.
  * **JSON (`.json`):** Formato jerárquico (`orient="records"`, `indent=2`, `force_ascii=False`).
  * **Excel (`.xlsx`):** Formato enriquecido mediante el motor `openpyxl`.

### 3. `notebook/limpieza/`
Aplica las reglas de negocio y calidad de datos necesarias para preparar la información antes de su consumo analítico:
* Eliminación de duplicados exactos e inconsistencias de claves compuestas.
* Limpieza de cadenas de texto (eliminación de espacios al inicio/final con `.strip()`).
* Estandarización de columnas categóricas (mapeo a conjuntos finitos permitidos en mayúsculas o tipo título).
* Parseo robusto de fechas multiformato mediante `datetime.strptime` o `pd.to_datetime`.
* Manejo de valores nulos o inválidos (descarte controlado o imputación justificada).

### 4. `notebook/consultas/` (Historias de Usuario HU Q01)
Implementa las consultas de negocio requeridas usando Pandas:
* Filtrado booleano de estados específicos (ej. finalizados, pendientes).
* Detección y auditoría de duplicados o anomalías en relaciones foráneas.
* Conteo de frecuencias con `value_counts()`.
* Agrupaciones complejas (`groupby`) y ordenamientos (`nlargest`, `sort_values`).
* Exportación automática de cada resultado individual a archivos `.csv` en la carpeta correspondiente.

### 5. `notebook/graficas/` (Historias de Usuario HU G01)
Genera visualizaciones de calidad profesional listas para presentación y toma de decisiones:
* **Configuración visual:** Títulos descriptivos, nombres claros en ambos ejes (`xlabel`, `ylabel`), formateo de etiquetas, tamaños controlados (`figsize=(8, 5)`) y ajuste de márgenes (`plt.tight_layout()`).
* **Resolución:** Exportación con `dpi=120` para nitidez adecuada en reportes y documentación.
* **Reporte en consola:** Imprime la ruta absoluta de cada archivo generado y redacta conclusiones clave cuantitativas, indicando hallazgos relevantes y recomendaciones técnicas para el backend (como validaciones de fechas y uso de códigos HTTP 409).

---

## 💾 Gestión de la Carpeta `datos/`

La carpeta `datos/` se encuentra excluida en el archivo `.gitignore` para evitar almacenar archivos binarios y datos generados en el control de versiones:
* Al clonar el proyecto por primera vez, `datos/` no existirá o estará vacía.
* No es necesario subirla al repositorio: basta con ejecutar los scripts de simulación y exportación para reconstruir exactamente la misma información gracias a las semillas reproducibles fijadas en el código.
