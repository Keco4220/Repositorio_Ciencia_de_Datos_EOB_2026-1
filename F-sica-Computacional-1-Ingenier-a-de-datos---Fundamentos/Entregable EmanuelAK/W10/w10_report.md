# W10 Report — Particionamiento + Partition Pruning

**Fecha:** 2026-05-19  
**Dataset:** `silver_planet_v3` (6 087 planetas — NASA Exoplanet Archive)  
**Columna de partición elegida:** `disc_era`

---

## 1. Evidencia de particionamiento

Se exportó `silver_planet_v3` a archivos Parquet individuales usando `COPY ... TO` de DuckDB, con una carpeta por valor de `disc_era`:

```
partitioned/
├── disc_era=pre-2000/data.parquet
├── disc_era=2000s/data.parquet
├── disc_era=2010s/data.parquet
├── disc_era=2020s/data.parquet
└── disc_era=unknown/data.parquet
```

---

## 2. Número de archivos generados

**5 archivos Parquet** — uno por cada valor de `disc_era`.

---

## 3. Resumen por partición

| disc_era | filas | tamaño | % del total |
|---|---|---|---|
| pre-2000 | 30 | 5.2 KB | 0.49% |
| 2000s | 380 | 29.0 KB | 6.24% |
| 2010s | 3 683 | 224.2 KB | 60.51% |
| 2020s | 1 993 | 137.2 KB | 32.74% |
| unknown | 1 | 2.3 KB | 0.02% |
| **TOTAL** | **6 087** | **397.9 KB** | 100% |

El skew es notable: la partición `2010s` concentra el 60.5% de los datos, reflejo del boom de descubrimientos de la misión Kepler (2009–2018).

---

## 4. Evidencia de pruning

Se comparó el plan `EXPLAIN ANALYZE` de la misma query sobre la tabla completa vs. una sola partición:

| escenario | filas escaneadas | archivos abiertos | reducción |
|---|---|---|---|
| Sin pruning (`silver_planet_v3`) | 6 087 | 1 (tabla entera) | — |
| Pruning `disc_era=2010s` | 3 683 | 1 parquet | **−39.5%** |
| Pruning `disc_era=2020s` | 1 993 | 1 parquet | **−67.3%** |
| Pruning `disc_era=pre-2000` | 30 | 1 parquet | **−99.5%** |

El plan con pruning muestra `Total Files Read: 1` y `3,683 rows` en el `TABLE_SCAN`, confirmando que los otros 4 archivos no se abren.

---

## 5. Archivo de EXPLAIN ANALYZE

Ver: `docs/w10b_explain_analyze_pruning.txt`

---

## 6. Filtro de pruning utilizado

```sql
SELECT discoverymethod_canon, COUNT(*) AS n
FROM read_parquet('.../disc_era=2010s/data.parquet')
GROUP BY discoverymethod_canon
ORDER BY n DESC;
```

El filtro es **`disc_era = '2010s'`**. Al leer directamente el archivo de esa partición, el motor solo abre ese Parquet y omite los demás. La reducción es del 39.5% (2 404 filas menos escaneadas). Para `pre-2000` el pruning alcanza el 99.5%.

---

## 7. Decisión de partición

Se eligió `disc_era` como columna de partición por:

- **Cardinalidad baja y fija:** 5 valores → 5 archivos (sin riesgo de explosión).
- **Patrón de consulta natural:** analistas filtran por era temporal con frecuencia (tendencias, comparaciones decadales).
- **Columna estable:** los registros históricos no cambian de era, por lo que las particiones pasadas son inmutables.
- **Tamaños manejables:** la partición más grande (2010s, 224 KB) es grande en proporción, pero en términos absolutos es trivial para un Parquet.

---

## 8. ¿Por qué `disc_era` sí?

`disc_era` cumple los tres criterios de una buena columna de partición:

1. **Baja cardinalidad:** evita la explosión de small files.
2. **Aparece en filtros reales:** preguntas como *¿cómo cambió la distribución de métodos de detección por década?* usan este campo directamente.
3. **Distribución no trivial:** aunque hay skew (2010s domina), las eras tienen sentido semántico propio y el pruning tiene valor incluso para la partición grande.

---

## 9. ¿Qué otra columna evaluaría?

Evaluaría `discoverymethod_canon`, pero la descartaría (ver punto 10). Una segunda opción viable en un escenario de más datos sería **`disc_year_int`** agrupado por año, que daría ~35 particiones con distribución más uniforme y permitiría pruning muy fino para análisis de años recientes. Sin embargo, con solo 6 087 filas generaría demasiados archivos pequeños.

---

## 10. Riesgo de *small files*

Si se particionara por `discoverymethod_canon`, **7 de 11 particiones** tendrían menos de 50 filas:

| método | filas | riesgo |
|---|---|---|
| disk_kinematics | 1 | ⚠ SMALL FILE |
| pulsation_timing_variations | 2 | ⚠ SMALL FILE |
| astrometry | 6 | ⚠ SMALL FILE |
| pulsar_timing | 8 | ⚠ SMALL FILE |
| orbital_brightness_modulation | 9 | ⚠ SMALL FILE |
| eclipse_timing_variations | 17 | ⚠ SMALL FILE |
| transit_timing_variations | 39 | ⚠ SMALL FILE |
| imaging | 91 | OK |
| microlensing | 265 | OK |
| radial_velocity | 1 161 | OK |
| transit | 4 488 | OK |

En un sistema distribuido (Spark/S3/Athena), abrir un archivo Parquet implica una operación de metadata independientemente de cuántos bytes contiene. Un archivo de 1 fila es casi todo overhead. Además, `transit` acapara el 73.7% → el pruning ayudaría poco en la práctica para la mayoría de las queries.

---

## 11. Reflexión breve

El particionamiento es una decisión de **diseño físico**, no lógico. El esquema lógico (`silver_planet_v3`) no cambia; solo cambia cómo se almacenan los datos en disco. La clave es que la columna de partición sea la misma que aparece más frecuentemente en el `WHERE` de las queries de producción. Si no se conocen esos patrones de acceso, particionar es una apuesta. En este caso, `disc_era` tiene justificación semántica fuerte: los exoplanetas se estudian históricamente por época de descubrimiento.

---

## 12. ¿Cuándo particionar ayuda?

- Datasets de **GB o TB** donde escanear todo es costoso en tiempo o dinero.
- Columna con **baja cardinalidad** y distribución razonable entre particiones.
- Queries que **filtran consistentemente** por esa columna.
- Sistemas que cobran por datos escaneados (Athena, BigQuery): el pruning ahorra dinero directamente.
- Necesidad de **reemplazar o purgar** un rango de datos sin tocar el resto (ej. re-ingestar solo el mes actual).

---

## 13. ¿Cuándo particionar empeora el diseño?

- Dataset **pequeño** (como aquí en términos absolutos): el overhead de gestionar múltiples archivos supera el beneficio del pruning. Una sola tabla en DuckDB es más eficiente para 6 087 filas.
- Columna de **alta cardinalidad**: genera cientos o miles de archivos, la mayoría minúsculos.
- **Skew severo**: si el 95% de los datos cae en una partición, el motor sigue leyendo casi todo y no hay ganancia real.
- Queries que **no filtran por la columna de partición**: el pruning nunca se activa.
- **Partición compuesta** con demasiadas dimensiones: la combinatoria genera archivos vacíos y el catálogo de metadata se vuelve un cuello de botella.
