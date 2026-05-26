# OPTIMADE Semiconductor Pipeline

## 📋 Descripción

Pipeline de descubrimiento y análisis de aleaciones semiconductoras utilizando datos de la **Materials Project API**. Este módulo implementa un arquitectura medallón (Bronze → Silver → Gold) para identificar candidatos óptimos de semiconductores según criterios físicos, económicos y de seguridad.

**Objetivo:** Filtrar y clasificar materiales semiconductores basado en:
- ✅ Propiedades ópticas (band gap cercano a Shockley-Queisser)
- ✅ Índice de refracción ideal
- ✅ Estabilidad mecánica (bulk modulus)
- ✅ Seguridad (exclusión de elementos tóxicos)
- ✅ Sostenibilidad (exclusión de elementos escasos)
- ✅ Scores DFT reales de Materials Project

---

## 📁 Estructura del Módulo

```
optimade-semiconductor-pipeline-master/
│
├── main.py                              # Pipeline principal
├── plots_annex.py                       # Generador de gráficas y visualizaciones
├── interactive_periodic_table.py        # Módulo para abrir tabla periódica
├── periodic_table_semiconductors.html   # Tabla periódica interactiva (HTML)
├── requirements.txt                     # Dependencias Python
│
├── data/                                # Datos (medallón)
│   ├── raw/                            # Bronze: datos crudos de Materials Project
│   │   └── materials_raw.json
│   ├── bronze/                         # Bronze: datos ingestados
│   │   ├── materials_bronze.parquet
│   │   └── materials_bronze.csv
│   ├── silver/                         # Silver: datos limpios y enriquecidos
│   │   ├── materials_silver.parquet
│   │   └── materials_silver_enriched.csv
│   └── gold/                           # Gold: candidatos finales (star-schema)
│       ├── top_semiconductors.parquet
│       ├── top_semiconductor_candidates.csv
│       ├── alloy_candidates.csv
│       ├── best_semiconductor_alloys.csv
│       └── elements_analysis.csv
│
└── artifacts/                           # Reportes y evidencias
    ├── evidence/
    │   └── raw_evidence.json           # Trazabilidad SHA-256
    ├── quality/
    │   └── silver_quality.csv          # Métricas de calidad
    ├── explain/
    │   └── gold_explain.txt            # EXPLAIN ANALYZE de queries Gold
    ├── timings/
    │   └── [ejecución y timings]
    └── reports/
        └── semiconductor_report.pdf    # Reporte ejecutivo
```

---

## 🔬 Constantes Físicas Implementadas

| Parámetro | Valor | Referencia |
|-----------|-------|-----------|
| **SQ Band Gap** | 1.34 eV | Shockley-Queisser (límite Auger) |
| **Si Reference** | 1.12 eV | Silicio (benchmark industrial) |
| **Ideal Refractive Index** | 2.5 - 4.0 | Rango óptimo para fotónica |
| **Ideal Bulk Modulus** | 130 GPa | Estabilidad mecánica objetivo |

---

## 🛡️ Filtros de Seguridad y Sostenibilidad

### 1. **Elementos Tóxicos (Exclusión RoHS)**
```python
TOXIC = {"Hg", "Be", "Tl", "Pb", "Th", "U", "Po", "Ra", "Ac", "Pu"}
```
Mercurio, Berilio, Talio, Plomo (toxicidad humana)  
Torio, Uranio, Polonio, Radio (radiactividad)

### 2. **Elementos Escasos (Riesgo de Cadena de Suministro)**
```python
SCARCE = {
    # Lantánidos críticos (EU/US DoE)
    "Ho", "Er", "Tm", "Tb", "Sm", "Nd", "Pr", "Ce", "Eu", "Gd", "Dy", "La", "Lu", "Yb",
    # Platinoides (~5 ppb abundancia crustal, ~$30k/kg)
    "Os", "Ir", "Re", "Ru", "Rh", "Pt",
    # Especiales
    "Y",   # Itrio (crítico en fotónica)
    "Cs",  # Cesio (subproducto de minería de Li, supply limitado)
}
```

### 3. **Elementos con Riesgo Medioambiental**
```python
ENV_RISK = {"Cd", "Co", "Ni", "Mn", "V", "Cr", "Mo", "W"}
```
Bioamplificación, bioacumulación, impacto en ecosistemas acuáticos.

---

## 🏗️ Arquitectura Medallón

### **Bronze Layer** (Ingesta)
- ✅ Descarga raw de Materials Project API
- ✅ Cálculo de SHA-256 para cada material
- ✅ Almacenamiento en Parquet para eficiencia

### **Silver Layer** (Limpieza + Enriquecimiento)
- ✅ Tipificación de datos
- ✅ Manejo de valores nulos
- ✅ Cálculo de características derivadas (distancia a banda prohibida óptima, etc.)
- ✅ Aplicación de filtros de seguridad/sostenibilidad
- ✅ **JOINs M:N** para composición química vs. propiedades

### **Gold Layer** (Analytics + Star-Schema)
- ✅ Agregaciones por sistema cristalino, composición, estructura
- ✅ Ranking por score de idoneidad como semiconductor
- ✅ **EXPLAIN ANALYZE** de queries complejas
- ✅ Fact table: materiales semiconductores
- ✅ Dim tables: elementos, sistemas cristalinos, propiedades

---

## 🚀 Instalación y Uso

### 1. Configurar API Key
```bash
# Crear archivo .env en la carpeta del módulo
echo "MP_API_KEY=tu_api_key_aqui" > .env
```

Obtener API Key en: https://materialsproject.org/api

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecutar pipeline
```bash
python main.py
```

**Salida esperada:**
- Tablas Parquet en `data/`
- Reportes CSV en `data/gold/`
- Reporte PDF en `artifacts/reports/semiconductor_report.pdf`
- **Tabla periódica interactiva se abre automáticamente** en el navegador (al finalizar)
- Archivo HTML disponible en: `periodic_table_semiconductors.html`

---

## 📊 Salidas del Pipeline

### Archivos Generados

| Archivo | Formato | Descripción |
|---------|---------|-------------|
| `materials_bronze.parquet` | Parquet | Datos crudos ingestados |
| `materials_silver.parquet` | Parquet | Datos limpios y enriquecidos |
| `top_semiconductors.parquet` | Parquet | Candidatos filtrados (Gold) |
| `best_semiconductor_alloys.csv` | CSV | Top 10-20 aleaciones recomendadas |
| `elements_analysis.csv` | CSV | Análisis de elemento por elemento |
| `semiconductor_report.pdf` | PDF | Reporte ejecutivo con gráficas |
| `silver_quality.csv` | CSV | Métricas de calidad (completitud, duplicados) |
| `raw_evidence.json` | JSON | Trazabilidad SHA-256 |
| `gold_explain.txt` | TXT | Query plans (EXPLAIN ANALYZE) |

### Visualizaciones
- **Tabla periódica interactiva** con colores por idoneidad como semiconductor
- **Gráficas de distribución** de band gaps, índices de refracción, bulk modulus
- **Scatter plots** de propiedades vs. toxicidad/escasez
- **Histogramas** de sistemas cristalinos más frecuentes

---

## 🔍 Módulo `interactive_periodic_table.py`

Módulo para visualizar la tabla periódica de semiconductores en el navegador.

### Funciones

**`open_explorer()`**
- Abre automáticamente `periodic_table_semiconductors.html` en el navegador por defecto
- Se ejecuta automáticamente al finalizar el pipeline en `main.py`
- Usa solo bibliotecas estándar de Python (`webbrowser`, `pathlib`)
- Compatible con Windows, macOS y Linux

### Uso manual
```bash
python interactive_periodic_table.py
```

---

## 🔧 Parámetros Configurables

Editar en `main.py`:

```python
# ── Physical constants ───────────────────────────────────────────────
SQ_EG   = 1.34          # Band gap Shockley-Queisser (eV)
N_MID   = 3.25          # Índice refracción ideal (centro)
N_HW    = 0.75          # Half-width ideal n (rango: [2.5, 4.0])
BM_IDEAL = 130.0        # Bulk modulus ideal (GPa)

# ── Query limits ────────────────────────────────────────────────────
LIMIT = 1000            # Número máximo de materiales a descargar
```

---

## 📈 Casos de Uso

1. **Descubrimiento de nuevos semiconductores** para celdas solares
2. **Screening rápido** de aleaciones para fotónica
3. **Evaluación de sostenibilidad** basada en escasez de elementos
4. **Análisis de viabilidad económica** (exclusión de platinoides)
5. **Identificación de alternativas** a Si/GaAs seguras y escalables

---

## 🔗 Referencias

- **Shockley-Queisser Limit:** Shockley, W., & Queisser, H. J. (1961). "Detailed Balance Limit of Efficiency of p-n Junction Solar Cells." *Journal of Applied Physics*, 32(3), 510-519.

- **Materials Project:** Jain, A., et al. (2013). "The Materials Project: A materials genome approach to accelerating materials innovation." *APL Materials*, 1(1), 011002.

- **RoHS Directive:** European Commission. Directive 2011/65/EU (Restriction of Hazardous Substances).

- **Critical Minerals:** U.S. Department of Energy & European Commission. Strategic Review of Critical Minerals (2022-2023).

---

## 📝 Notas

- El pipeline requiere conexión a internet para descargar datos de Materials Project
- Las queries de Gold usan **window functions y CTEs** para mayor eficiencia
- Todos los artefactos incluyen **timestamp** para rastreabilidad
- Los scores DFT son **directamente de Materials Project** (calculados experimentalmente/teóricamente)

---

**Autor:** Emanuel A. Osorio Bracho  
**Última actualización:** 25 de Mayo de 2026  
**Status:** Production-ready
