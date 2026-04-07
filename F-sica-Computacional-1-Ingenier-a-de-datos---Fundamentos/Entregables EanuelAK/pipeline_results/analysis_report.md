# Reporte de Análisis Exoplanetario — Pipeline Entregable

**Fecha de generación:** 2026-04-07T01:01:09.823681+00:00

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
