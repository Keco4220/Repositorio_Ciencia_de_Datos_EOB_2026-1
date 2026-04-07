# Reporte de Análisis Exoplanetario — Pipeline Entregable

**Fecha de generación:** 2026-04-07T01:15:08.088299+00:00

## Resumen Ejecutivo

Este reporte documenta el análisis enriquecido del dataset de exoplanetas de la NASA,
con tres columnas adicionales calculadas para análisis profundo.

## Columnas Añadidas

1. **disc_decade**: Década de descubrimiento (agrupación 10 años)
   - Calculada como: `(disc_year // 10) * 10`
   - Facilita análisis histórico por períodos

2. **pl_density_earth**: Densidad del planeta relativa a la Tierra
   - Calculada como: `pl_bmasse / (pl_rade ^ 3)`
   - Métrica física para caracterización planetaria

3. **insolation_class**: Clasificación de temperatura de equilibrio
   - Categorías: cold (<=250 K), temperate (250-500 K), hot (500-1000 K), extreme (>1000 K)
   - Basada en `pl_eqt` (temperatura de equilibrio del planeta)

## Estadísticas Generales

| Métrica | Valor |
|---------|-------|
| Total de filas procesadas | 6,087 |
| Filas con década de descubrimiento | 6,086 |
| Densidad media (Earth) | 2.436898 |
| Densidad mínima | 0.005487 |
| Densidad máxima | 2517.401320 |
| Descubrimientos en 1992 | 2 |
| Descubrimientos en 1994 | 1 |
| Descubrimientos en 1995 | 1 |
| Descubrimientos en 1996 | 6 |
| Descubrimientos en 1997 | 1 |
| Descubrimientos en 1998 | 6 |
| Descubrimientos en 1999 | 13 |
| Descubrimientos en 2000 | 16 |
| Descubrimientos en 2001 | 12 |
| Descubrimientos en 2002 | 29 |
| Descubrimientos en 2003 | 22 |
| Descubrimientos en 2004 | 27 |
| Descubrimientos en 2005 | 36 |
| Descubrimientos en 2006 | 32 |
| Descubrimientos en 2007 | 52 |
| Descubrimientos en 2008 | 63 |
| Descubrimientos en 2009 | 91 |
| Descubrimientos en 2010 | 98 |
| Descubrimientos en 2011 | 135 |
| Descubrimientos en 2012 | 139 |
| Descubrimientos en 2013 | 128 |
| Descubrimientos en 2014 | 869 |
| Descubrimientos en 2015 | 155 |
| Descubrimientos en 2016 | 1,496 |
| Descubrimientos en 2017 | 152 |
| Descubrimientos en 2018 | 315 |
| Descubrimientos en 2019 | 196 |
| Descubrimientos en 2020 | 235 |
| Descubrimientos en 2021 | 554 |
| Descubrimientos en 2022 | 369 |
| Descubrimientos en 2023 | 326 |
| Descubrimientos en 2024 | 260 |
| Descubrimientos en 2025 | 241 |
| Descubrimientos en 2026 | 8 |
| Descubrimientos en década de 1990s | 30 |
| Descubrimientos en década de 2000s | 380 |
| Descubrimientos en década de 2010s | 3,683 |
| Descubrimientos en década de 2020s | 1,993 |


## Distribución por Clase de Insolación

| Clase | Cantidad | Porcentaje |
|-------|----------|-----------|
| Fríos (<=250 K) | 83 | 1.36% |
| Templados (250-500 K) | 732 | 12.03% |
| Calientes (500-1000 K) | 2,133 | 35.04% |
| Extremos (>1000 K) | 1,600 | 26.29% |
| Desconocidos | 1,539 | 25.28% |

## Archivos Generados

- **CSV**: `analysis_enhanced.csv` — Datos completos con columnas enriquecidas
- **Base de datos**: `analysis_exoplanets.db` — Índices optimizados para consultas rápidas
- **Reporte**: Este documento

## Notas Técnicas

- Valores nulos: Se preservan como campos vacíos en el CSV e índices en SQLite
- Precisión numérica: 6 decimales para densidades
- Encoding: UTF-8 para todos los archivos
- Índices SQLite: `disc_decade`, `insolation_class` para consultas optimizadas

---
*Generado automáticamente por pipeline.py*
