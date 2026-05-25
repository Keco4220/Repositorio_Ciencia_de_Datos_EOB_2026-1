# Repositorio Ciencia de Datos EOB 2026-1

Repositorio para el curso **Física Computacional 1: Ingeniería de Datos I (Fundamentos)** - Universidad de los Andes, Bogotá.

**Estudiante:** Emanuel A. Osorio Bracho  
**Docente:** Ph.D. Santiago Echeverri Arteaga  
**Semestre:** 2026-1  
**Programa:** Física - Ingeniería de Datos

---

## 📚 Descripción General

Este repositorio contiene:
- **Entregables** del curso (Semanas 1-11)
- **Notebooks** de clase con soluciones
- **Pipeline ETL** reproducible para análisis de exoplanetas
- **Análisis de semiconductores** (módulo complementario)
- **Código modular** en `src/` para reutilización

### Dataset Principal
- **Fuente:** NASA Exoplanet Archive (TAP)
- **Tabla:** `pscomppars` (Planetary Systems Composite Parameters)
- **Objetivo:** Análisis reproducible siguiendo modelo Raw → Silver → Gold

---

## 📁 Estructura del Repositorio

```
Repositorio-Ciencia-de-Datos-EOB-2026-1/
│
├── README.md                                        # Este archivo (raíz del repo)
├── requirements.txt                                 # Dependencias Python
│
├── F-sica-Computacional-1-Ingenier-a-de-datos---Fundamentos/
│   ├── README.md                                   # Documentación del curso
│   ├── requirements.txt                            # Deps del curso
│   ├── .gitignore
│   │
│   ├── notebooks/                                  # 📖 Notebooks de clase (referencia)
│   │   ├── W01.ipynb                              # Semana 1: Intro + Entorno + Evidencia
│   │   ├── W02.ipynb                              # Semana 2: SQL Básico
│   │   ├── W03.ipynb                              # Semana 3: JOINs + CTEs + Cardinalidad
│   │   ├── W04.ipynb                              # Semana 4: Modelado Relacional
│   │   ├── W05.ipynb                              # Semana 5: Calidad de Datos
│   │   ├── W06.ipynb                              # Semana 6: ETL Raw→Silver
│   │   ├── W07B_student.ipynb                     # Semana 7B: Pipeline (versión estudiante)
│   │   ├── W07B_teacher.ipynb                     # Semana 7B: Pipeline (versión profesor)
│   │   ├── W08_demo.ipynb                         # Semana 8: Demostración
│   │   ├── w08_report.ipynb                       # Semana 8: Reporte
│   │   ├── W09_assignment_student.ipynb           # Semana 9: Asignación (estudiante)
│   │   ├── W10_student.ipynb                      # Semana 10: Asignación (estudiante)
│   │   └── W11_student.ipynb                      # Semana 11: Asignación (estudiante)
│   │
│   ├── Entregable EmanuelAK/                       # 📌 CARPETA PRINCIPAL DE ENTREGABLES
│   │   ├── W01/                                   # Entregable Semana 1
│   │   │   ├── W01_resuelto.ipynb
│   │   │   ├── w01a_run.md
│   │   │   ├── w01b_checks.md
│   │   │   ├── w01b_raw_evidence.json
│   │   │   ├── decisions_log.md
│   │   │   └── glossary.md
│   │   │
│   │   ├── W02/                                   # Entregable Semana 2 (SQL Básico)
│   │   │   ├── decisions_log.md
│   │   │   └── w02a_sql_practice.md
│   │   │
│   │   ├── W03/                                   # Entregable Semana 3 (JOINs)
│   │   │   ├── decisions_log.md
│   │   │   ├── w03_join_case.md
│   │   │   └── w03_sql_practice.md
│   │   │
│   │   ├── W04/                                   # Entregable Semana 4 (Modelado)
│   │   │   ├── decisions_log.md
│   │   │   ├── data_contract_v1.json
│   │   │   ├── data_contract_silver_v1.json
│   │   │   ├── quality_w03a.csv
│   │   │   ├── w03b_silver_report.md
│   │   │   └── w04a_quality_report.md
│   │   │
│   │   ├── W05/                                   # Entregable Semana 5 (Calidad)
│   │   │   ├── decisions_log.md
│   │   │   ├── w05_explain_q1.txt
│   │   │   └── w05_perf_report.md
│   │   │
│   │   ├── W06/                                   # Entregable Semana 6 (ETL)
│   │   │   ├── decisions_log.md
│   │   │   ├── data_contract.md
│   │   │   ├── w06a_evidence.md
│   │   │   ├── w06b_gold_report.md
│   │   │   ├── gold_by_discoverymethod.csv
│   │   │   └── gold_by_host.csv
│   │   │
│   │   ├── W07/                                   # Entregable Semana 7 (Pipeline)
│   │   │   ├── decisions_log.md
│   │   │   ├── w06b_run_log.md
│   │   │   ├── w06b_run_report.json
│   │   │   └── w06b_stage_timings.csv
│   │   │
│   │   ├── W08/                                   # Entregable Semana 8
│   │   │   ├── decisions_log.md
│   │   │   └── w08_report.md
│   │   │
│   │   ├── W09/                                   # Entregable Semana 9
│   │   │   ├── decisions_log_w09.md
│   │   │   └── W09_assignment_student.ipynb
│   │   │
│   │   ├── W10/                                   # Entregable Semana 10
│   │   │   └── [pendiente]
│   │   │
│   │   ├── W11/                                   # Entregable Semana 11
│   │   │   └── [pendiente]
│   │   │
│   │   ├── optimade-semiconductor-pipeline-master/  # 🔧 Análisis de semiconductores
│   │   │   ├── main.py                            # Script principal
│   │   │   ├── plots_annex.py                     # Generador de gráficas
│   │   │   ├── requirements.txt
│   │   │   ├── periodic_table_semiconductors.html # Tabla periódica interactiva
│   │   │   ├── artifacts/                         # Outputs de ejecución
│   │   │   └── data/                              # Datos de semiconductores
│   │   │
│   │   ├── w03a_quality_report.md
│   │   ├── w03a_quality_2026-03-09T13-45-04.171805+00-00.csv
│   │   └── w03b_silver_report.md
│   │
│   ├── src/                                        # 🔧 Código modular reutilizable
│   │   ├── __init__.py
│   │   ├── ingest/                               # Ingesta de datos
│   │   │   └── download_exoplanets.py
│   │   ├── pipeline/                             # Pipelines ETL
│   │   │   └── w07_pipeline.py
│   │   └── utils/                                # Utilidades
│   │       ├── paths.py                          # Resolución de rutas
│   │       └── db.py                             # Conexiones DuckDB
│   │
│   ├── data/                                      # 📊 Datos (NO versionado)
│   │   ├── raw/
│   │   │   └── pscomppars.csv                    # Datos originales de exoplanetas
│   │   ├── silver/                               # [Datos procesados]
│   │   └── gold/                                 # [Métricas finales]
│   │
│   ├── artifacts/                                # 📦 Artefactos y evidencias
│   │   └── w01b_raw_evidence_1770177020.json
│   │
│   └── docs/                                      # 📚 Documentación
│       ├── examples/
│       │   ├── w02a_sql_practice_example.md
│       │   ├── w02b_join_case_example.md
│       │   └── w02b_sql_practice_example.md
│       └── templates/
│           ├── data_contract_patch_w06a.md
│           ├── decisions_log_entry_w06a.md
│           ├── decisions_log.md
│           ├── h2_checklist.md
│           ├── h2_final_checklist.md
│           ├── w02a_sql_practice.md
│           ├── w02b_join_case.md
│           ├── w02b_sql_practice.md
│           ├── w03b_silver_report.md
│           ├── w04a_perf_report.md
│           ├── w04b_index_report.md
│           ├── w05b_gold_report.md
│           └── w06a_run_log.md
```

---

## 🛠️ Tecnologías Utilizadas

- **Python 3.8+**
- **SQL (DuckDB)** - Base de datos in-memory
- **Pandas** - Manipulación de datos
- **Jupyter Notebooks** - Análisis interactivo
- **JSON Schema** - Contratos de datos
- **Git** - Control de versiones

---

## 🚀 Cambios Recientes (2026-05-25)

### Reorganización de Estructura
1. **Renombramiento de carpeta:**
   - `Entregables EanuelAK` → `Entregable EmanuelAK` (corrección de nombre)

2. **Complementación de notebooks:**
   - Añadido: W07B_student.ipynb, W07B_teacher.ipynb
   - Añadido: W08_demo.ipynb, w08_report.ipynb
   - Añadido: W09_assignment_student.ipynb, W10_student.ipynb, W11_student.ipynb

3. **Organización de entregables:**
   - Estructura por semanas (W01-W11) dentro de `Entregable EmanuelAK/`
   - Cada semana contiene: notebook, reporte, decisiones_log, artefactos

4. **Inclusión de módulo de semiconductores:**
   - Carpeta: `Entregable EmanuelAK/optimade-semiconductor-pipeline-master/`
   - Propósito: Análisis complementario de semiconductores
   - Incluye: Pipeline de datos, visualizaciones, tabla periódica interactiva

5. **Eliminación de archivos obsoletos:**
   - `Entregables EanuelAK/` (versión antigua)
   - `requirements 2.txt`
   - README.md anterior en raíz

---

## 📋 Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone https://github.com/fisica-computacional-2026-1/Repositorio-Ciencia-de-Datos-EOB-2026-1.git
cd Repositorio-Ciencia-de-Datos-EOB-2026-1
```

### 2. Crear entorno virtual
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell
source .venv/bin/activate  # macOS/Linux
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
cd F-sica-Computacional-1-Ingenier-a-de-datos---Fundamentos
pip install -r requirements.txt
```

### 4. Para análisis de semiconductores
```bash
cd Entregable\ EmanuelAK/optimade-semiconductor-pipeline-master
pip install -r requirements.txt
python main.py
```

---

## 📖 Guía de Uso

### Ejecutar notebooks de clase
```bash
cd F-sica-Computacional-1-Ingenier-a-de-datos---Fundamentos
jupyter notebook notebooks/
```

### Ver entregables completados
Los entregables están organizados por semana en:
```
F-sica-Computacional-1-Ingenier-a-de-datos---Fundamentos/Entregable EmanuelAK/W01/ ... W11/
```

Cada carpeta contiene:
- Notebook con solución
- Reportes markdown
- Registro de decisiones (`decisions_log.md`)
- Datos intermedios/finales
- Evidencias de ejecución

---

## 🔗 Remotos Git

El repositorio está vinculado a dos remotos:

```
origin    → https://github.com/fisica-computacional-2026-1/Repositorio-Ciencia-de-Datos-EOB-2026-1.git
personal  → https://github.com/Keco4220/Repositorio_Ciencia_de_Datos_EOB_2026-1.git
```

Para hacer push:
```bash
git push origin main      # Push al remoto oficial
git push personal main    # Push al remoto personal
```

---

## 📝 Notas

- Los datos crudos (`data/raw/`) no se versionan en Git
- Los artefactos de ejecución se guardan en `artifacts/`
- Cada entregable incluye un `decisions_log.md` documentando las decisiones de diseño
- El análisis de semiconductores es modular y puede ejecutarse independientemente

---

## 👤 Autor

**Emanuel A. Osorio Bracho**  
Estudiante de Física - Ingeniería de Datos  
Universidad de los Andes, Bogotá  
2026-1

---

**Última actualización:** 25 de Mayo de 2026
