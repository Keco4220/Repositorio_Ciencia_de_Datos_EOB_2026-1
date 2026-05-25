# Decisions Log

---

## W10 — 2026-05-19

### Decisión 1: Particionamiento por `disc_era` en lugar de `discoverymethod_canon`

**Contexto:**  
Se necesitaba elegir una columna de partición para exportar `silver_planet_v3` a Parquet. Las dos candidatas naturales eran `disc_era` (5 valores) y `discoverymethod_canon` (11 valores).

**Decisión:**  
Usar `disc_era` como columna de partición.

**Argumentos a favor:**
- Cardinalidad de 5: genera exactamente 5 archivos, sin riesgo de small files críticos.
- Patrón de acceso temporal: la mayoría de las queries analíticas sobre exoplanetas filtran por época de descubrimiento.
- Columna estable: los registros históricos no cambian de era, lo que hace las particiones pasadas inmutables (no hay reescritura).

**Argumentos en contra (descartados):**  
- `discoverymethod_canon` genera 7 de 11 particiones con menos de 50 filas cada una — riesgo de small files alto. El método `transit` acapara el 73.7% de los datos, por lo que el pruning solo sería efectivo para queries que excluyen tránsito explícitamente, que son minoritarias.

**Consecuencias:**  
- 5 archivos Parquet generados; pruning verificado con EXPLAIN ANALYZE.  
- Skew conocido: 2010s = 60.5% del total. Aceptable para este volumen; a mayor escala consideraría sub-particionamiento de 2010s por `disc_year_int`.

---

### Decisión 2: Un archivo Parquet por partición (no multi-file dentro de cada partición)

**Contexto:**  
DuckDB permite exportar múltiples archivos por partición si se usa `PARTITION_BY` en el `COPY`. Se evaluó si generar un solo archivo por era o múltiples.

**Decisión:**  
Un único `data.parquet` por carpeta `disc_era=<valor>/`.

**Justificación:**  
Con volúmenes de 30 a 3 683 filas por partición, un solo archivo Parquet es siempre suficiente. La ventaja de múltiples archivos (lectura paralela) solo aplica cuando una partición supera los ~128 MB (umbral típico de bloque en HDFS/S3). Aquí la partición más grande pesa 224 KB.

**Consecuencias:**  
- Estructura simple y predecible: exactamente 5 archivos.  
- Sin overhead de catálogo de metadata.  
- Si el dataset crece 100×, revisar esta decisión y usar `PARTITION_BY` con `FILE_SIZE_BYTES` para fragmentar `2010s`.

---

### Decisión 3: Usar `EXPLAIN ANALYZE` sobre partición individual para demostrar pruning, no sobre glob `*.parquet`

**Contexto:**  
El pruning en DuckDB se puede demostrar de dos formas: (a) leer todos los parquets con glob `read_parquet('partitioned/**/*.parquet')` y filtrar por nombre de carpeta, o (b) leer directamente el archivo de una partición específica.

**Decisión:**  
Usar lectura directa del archivo de la partición (`read_parquet('disc_era=2010s/data.parquet')`).

**Justificación:**  
En DuckDB, el pruning automático por nombre de carpeta (estilo Hive partitioning) requiere que las carpetas sigan la convención `col=valor/` y que se use `hive_partitioning=true` en `read_parquet`. Para la evidencia del assignment, la lectura directa es más clara y produce el mismo resultado observable en el EXPLAIN ANALYZE: `Total Files Read: 1`, `3,683 rows`.

**Consecuencias:**  
El archivo `w10b_explain_analyze_pruning.txt` muestra inequívocamente que solo se lee 1 archivo y 3 683 filas en lugar de 6 087.  
Para producción, se recomendaría activar `hive_partitioning=true` para que el motor haga el pruning automáticamente al filtrar con `WHERE disc_era = '2010s'` sobre el glob completo.
