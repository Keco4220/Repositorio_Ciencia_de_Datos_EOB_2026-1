# Física Computacional 1: Ingeniería de Datos I (Fundamentos)

**Docente:** Ph.D. Santiago Echeverri Arteaga  
**Nivel:** Primer curso de la línea de Física Computacional  
**Objetivo:** Formar base sólida en SQL, diseño de datos, calidad y ETL reproducible sin infraestructura pesada

---

## 📋 Descripción del Curso

Este es el primer curso de la línea de **Física Computacional** del programa de Física:

1. **FC 1:** Ingeniería de Datos I — Fundamentos (local, sin Docker/Spark)
2. **FC 2:** Ingeniería de Datos II — Big Data con Spark (ZTF Objects+Lightcurves)
3. **FC 3:** Ciencia de Datos / ML en Big Data (feature engineering + entrenamiento reproducible)
4. **FC 4:** Deep Learning en Big Data (pipelines para DL + inferencia a escala)

### Dataset
- **Fuente:** NASA Exoplanet Archive (TAP)
- **Tabla:** `pscomppars` (Planetary Systems Composite Parameters)
- **Enfoque:** Análisis reproducible de exoplanetas descubiertos

### Modelo de Datos: Raw → Silver → Gold

```
RAW             SILVER              GOLD
[CSV/JSON]   →  [Tipado+Limpio] →  [Métricas/Marts]
                (Parquet)           (Tablas finales)
```

---

## 📁 Estructura del Repositorio

```
F-sica-Computacional-1-Ingenier-a-de-datos---Fundamentos/
│
├── README.md                          # Este archivo
├── .gitignore                         # Configuración de Git
├── requirements.txt                   # Dependencias Python
│
├── notebooks/                         # Notebooks de clase (referencia)
│   ├── W01.ipynb                     # Semana 1: Intro + Entorno + Evidencia
│   ├── W02.ipynb                     # Semana 2: SQL Básico (SELECT/WHERE/GROUP BY)
│   ├── W03.ipynb                     # Semana 3: JOINs + CTEs + Cardinalidad
│   ├── W04.ipynb                     # Semana 4: Modelado Relacional
│   ├── W05.ipynb                     # Semana 5: Calidad de Datos
│   └── W06.ipynb                     # Semana 6: ETL Raw→Silver
│
├── Entregables EanuelAK/              # 📌 CARPETA DE ENTREGABLES
│   ├── W01.ipynb                     # Entregable 1
│   ├── W02.ipynb                     # Entregable 2
│   ├── W03.ipynb                     # Entregable 3
│   ├── W04.ipynb                     # Entregable 4
│   ├── W05.ipynb                     # Entregable 5
│   └── W06.ipynb                     # Entregable 6
│
├── src/                               # Código fuente (módulos reutilizables)
│   ├── __init__.py
│   ├── ingest/
│   │   └── download_exoplanets.py   # Script de descarga de datos
│   ├── pipeline/
│   │   └── w07_pipeline.py          # Pipelines ETL
│   └── utils/
│       ├── paths.py                 # Resolución de rutas
│       └── db.py                    # Conexiones a DuckDB
│
├── data/                              # Datos (NO versionado)
│   ├── raw/
│   │   └── pscomppars.csv           # Datos originales descargados
│   ├── silver/                      # Datos limpios/tipados
│   └── gold/                        # Métricas finales
│
├── docs/                              # Documentación del proyecto
│   ├── examples/                    # Ejemplos de SQL y casos de uso
│   │   ├── w02a_sql_practice_example.md
│   │   ├── w02b_join_case_example.md
│   │   └── w02b_sql_practice_example.md
│   └── templates/                   # Plantillas de entregables
│       ├── data_contract_patch_w06a.md
│       ├── decisions_log_entry_w06a.md
│       ├── decisions_log.md
│       ├── w02a_sql_practice.md
│       ├── w02b_join_case.md
│       ├── w02b_sql_practice.md
│       ├── w03b_silver_report.md
│       ├── w04a_perf_report.md
│       ├── w04b_index_report.md
│       ├── w05b_gold_report.md
│       └── w06a_run_log.md
│
├── artifacts/                         # Evidencia generada
│   └── w01b_raw_evidence_1770177020.json
│
└── .git/                              # Control de versión
```

---

## 🚀 Guía de Inicio Rápido

### 1. Configurar Entorno

```bash
# Crear virtual environment
python -m venv .venv

# Activar (Linux/Mac)
source .venv/bin/activate

# Activar (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Descargar Datos

```bash
# Descargar CSV completo de NASA Exoplanet Archive
python -m src.ingest.download_exoplanets --format csv

# O con limit (útil para pruebas)
python -m src.ingest.download_exoplanets --format csv --limit 50000
```

### 3. Ejecutar Notebooks

Los notebooks se encuentran en dos ubicaciones:

- **`notebooks/`** — Para seguimiento en clase (referencia)
- **`Entregables EanuelAK/`** — Entregables completados

Ejecutar desde la carpeta de entregables:

```bash
cd Entregables EanuelAK
# Los notebooks ajustan automáticamente sus rutas
jupyter notebook W01.ipynb
```

---

## 📚 Especificaciones Técnicas

### Entorno Python
- **Versión:** Python 3.8+
- **Gestor de dependencias:** pip
- **Virtual environment:** .venv/

### Dependencias Principales
- **DuckDB:** Base de datos SQL embebida
- **Jupyter:** Notebooks interactivos
- **Pandas:** Manipulación de datos (opcional en algunos flujos)
- **Numpy:** Computación numérica

Véase [requirements.txt](requirements.txt) para lista completa.

### Base de Datos
- **Motor:** DuckDB (in-process SQL database)
- **Archivo persistente:** `data/exoplanets.duckdb`
- **Formato de datos:** 
  - Raw: CSV (desde NASA)
  - Silver: Parquet (limpio, tipado)
  - Gold: Tablas en DuckDB

### Rutas de Datos
```
data/
├── raw/              # Datos originales (no versionados)
├── silver/           # Datos limpios intermedio
├── gold/             # Métricas finales
└── exoplanets.duckdb # Base de datos local
```

---

## 📝 Estructura de Entregables

Cada semana corresponde a un entregable en la carpeta **`Entregables EanuelAK/`**:

| Semana | Notebook | Contenido |
|--------|----------|-----------|
| W01 | W01.ipynb | Intro + Setup + Entorno + Primera evidencia |
| W02 | W02.ipynb | SQL Básico: SELECT, WHERE, GROUP BY, agregaciones |
| W03 | W03.ipynb | JOINs avanzados, CTEs, validación de cardinalidad |
| W04 | W04.ipynb | Modelado relacional, design de esquema |
| W05 | W05.ipynb | Calidad de datos, reglas y validaciones |
| W06 | W06.ipynb | Pipeline ETL raw→silver, reproducibilidad |

### Cómo Trabajar con Entregables

1. **Abrir desde la carpeta de entregables:**
   ```bash
   cd Entregables EanuelAK
   jupyter notebook W01.ipynb
   ```

2. **Las rutas se resuelven automáticamente:**
   - Los notebooks ejecutan `os.chdir("..")` para ir a la carpeta principal
   - Los imports desde `src/` funcionan automáticamente
   - Acceso a `data/`, `docs/`, `artifacts/` ✓

3. **Guardar cambios:**
   - Jupyter guarda en `.ipynb` automáticamente
   - Los datos generados van a `data/`
   - La evidencia se guarda en `artifacts/`

---

## 🔄 Flujo de Trabajo ETL

### Raw → Silver
```python
# Lectura tipada y limpieza mínima
- Convertir tipos (string → int/float)
- Manejar nulos según reglas de negocio
- Validar rangos físicos (ej. masa > 0)
- Generar columnas canónicas
- Output: Parquet con schema definido
```

### Silver → Gold
```python
# Agregaciones y métricas
- Contar exoplanetas por método de descubrimiento
- Distribución por año
- Estadísticas por sistema planetario
- Output: Tablas finales en DuckDB (fact/dimension)
```

---

## 🛠️ Herramientas y Tecnologías

| Tool | Propósito | Versión |
|------|-----------|---------|
| **DuckDB** | Base de datos SQL | 1.4.4+ |
| **Jupyter** | Notebooks interactivos | 6.31.0+ |
| **Python** | Lenguaje | 3.8+ |
| **Pandas** | Manipulación datos (opcional) | 2.0+ |
| **Numpy** | Cálculo numérico | 2.0+ |

---

## 📖 Bibliografía y Recursos

### Preparación Local
1. **Martin Kleppmann** - *Designing Data-Intensive Applications* (DDIA)
   - Cap. 1-3: Confiabilidad, escalabilidad, mantenibilidad
   - Cap. 2: Modelos de datos y SQL

2. **DuckDB Documentation**
   - https://duckdb.org/docs/
   - SQL, import/export, EXPLAIN, performance

3. **NASA Exoplanet Archive**
   - https://exoplanetarchive.ipac.caltech.edu/
   - TAP Query Interface
   - PSCompPars documentation

4. **Kimball Group - Data Warehouse Design**
   - Star schema (facts/dimensions)
   - Conformed dimensions

### Recursos Compartidos
Materiales adicionales disponibles en el Drive del Curso

---

## ⚙️ Configuración y Notas Importantes

### Para Contribuidores
- **Branching:** Crear rama por feature/semana
- **Commits:** Descriptivos y atómicos
- **.gitignore:** Activo para datos, bases de datos y outputs
- **No comitear:** `data/`, `*.duckdb`, `artifacts/*.json`, outputs

### Reproducibilidad
- Todos los scripts son reproducibles (semilla fija en randomness)
- Las rutas son relativas (funciona en cualquier máquina)
- Documentación de decisiones en `docs/decisions_log.md`

### Troubleshooting
- **"Módulo src no encontrado":** Verificar que se ejecuta desde carpeta correcta
- **"CSV no descargado":** Ejecutar `python -m src.ingest.download_exoplanets`
- **"DuckDB corrupted":** Eliminar `data/exoplanets.duckdb` y regenerar

---

## 📧 Contacto y Soporte

**Docente:** Ph.D. Santiago Echeverri Arteaga

Para dudas sobre:
- Contenido del curso → Consulta en clase
- Setup técnico → Revisa troubleshooting arriba
- Dataset → Consulta NASA Exoplanet Archive

---

## 📄 Licencia

Este proyecto es de uso académico como parte del Programa de Física - Línea Computacional.

**Última actualización:** Marzo 2026
