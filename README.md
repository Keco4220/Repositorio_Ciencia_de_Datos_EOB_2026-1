# Repositorio de Física Computacional I: Ingeniería de Datos

**Autor:** Emanuel Osorio  
**Docente:** Ph.D. Santiago Echeverri Arteaga  
**Período:** 2026

---

## Descripción General

Este repositorio contiene los trabajos realizados en el curso **Física Computacional I: Ingeniería de Datos (Fundamentos)**. El proyecto se enfoca en el desarrollo de un pipeline de procesamiento de datos aplicado al análisis de exoplanetas del NASA Exoplanet Archive, utilizando técnicas de ingeniería de datos sin infraestructura de clusters o contenedores.

## Organización del Repositorio

```
Repositorio DS/
│
└── F-sica-Computacional-1-Ingenier-a-de-datos---Fundamentos/
    ├── Entregables EanuelAK/       Entregables semanales (W01-W06)
    ├── notebooks/                  Notebooks de referencia del curso
    ├── src/                        Módulos Python (ingesta, procesamiento, utilidades)
    ├── data/                       Capas de datos (raw, silver, gold)
    ├── docs/                       Documentación de decisiones y plantillas
    ├── artifacts/                  Evidencia generada (logs, evidencia JSON)
    ├── README.md                   Documentación técnica detallada
    ├── .gitignore                  Configuración de versioning
    └── requirements.txt            Dependencias del proyecto
```

## Contenido del Proyecto

### Entregables

Se han completado 6 notebooks correspondientes a 6 semanas de trabajo:

| Semana | Notebook | Contenido Principal |
|--------|----------|-------------------|
| W01 | W01.ipynb | Configuración del entorno, introducción al dataset y primera evidencia |
| W02 | W02.ipynb | SQL fundamental (SELECT, WHERE, GROUP BY, agregaciones en DuckDB) |
| W03 | W03.ipynb | Operaciones JOIN, CTEs y validación de cardinalidad en relaciones |
| W04 | W04.ipynb | Modelado relacional, diseño de esquema y normalización |
| W05 | W05.ipynb | Calidad de datos, reglas de validación y perfilado |
| W06 | W06.ipynb | Pipeline ETL reproducible (raw → silver) con transformaciones tipadas |

Cada entregable incluye código ejecutado, resultados y análisis desarrollado durante la semana.

### Estructura Técnica

**Módulo de Ingesta (`src/ingest/`):**
- Descarga automatizada del dataset PSCompPars desde NASA Exoplanet Archive
- Parámetros configurables para limitar volumen de datos

**Módulo de Utilidades (`src/utils/`):**
- Resolución de rutas relativas independiente del ambiente (paths.py)
- Gestión de conexiones a DuckDB (db.py)

**Capas de Datos:**
- **Raw:** Datos originales en formato CSV
- **Silver:** Datos limpios, tipados y validados en formato Parquet
- **Gold:** Agregaciones y métricas finales en tablas DuckDB

## Requisitos Técnicos

- Python 3.8 o superior
- DuckDB 1.4.4+ (base de datos SQL embebida)
- Jupyter Notebook 6.31.0+
- Pandas 2.0+ (manipulación de datos)
- NumPy 2.0+ (cálculo numérico)

Ver `requirements.txt` para la lista completa de dependencias.

## Instalación y Uso

1. **Navegar a la carpeta del curso:**
   ```bash
   cd F-sica-Computacional-1-Ingenier-a-de-datos---Fundamentos
   ```

2. **Configurar el entorno virtual:**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1  # Windows PowerShell
   # o
   source .venv/bin/activate     # Linux/Mac
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar los entregables:**
   ```bash
   cd Entregables EanuelAK
   jupyter notebook W01.ipynb
   ```

## Metodología

El proyecto sigue el modelo de procesamiento en capas establecido en el curso:

1. **Fase Raw:** Ingesta de datos originales sin transformaciones
2. **Fase Silver:** Limpieza, tipado y validación de datos
3. **Fase Gold:** Agregaciones, métricas y vistas analíticas

Cada fase incluye validaciones de calidad y documentación de decisiones tomadas.

## Información Adicional

Para documentación técnica detallada sobre configuración, depuración y detalles de implementación, consulte el [README técnico de la carpeta del curso](F-sica-Computacional-1-Ingenier-a-de-datos---Fundamentos/README.md).

---

**Versión:** 1.0  
**Última actualización:** Marzo 2026
