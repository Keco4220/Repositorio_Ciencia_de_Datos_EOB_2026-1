# Decisions Log

---

## W11 — 2026-05-19

### Decisión 1: `= 'transit'` en lugar de `LOWER(TRIM(...)) LIKE '%transit%'`

**Contexto:**  
La query baseline filtraba con `LOWER(TRIM(discoverymethod_canon)) LIKE '%transit%'`. El objetivo era capturar cualquier variante del método "transit".

**Decisión:**  
Usar `discoverymethod_canon = 'transit'` en la query optimizada.

**Justificación:**  
`discoverymethod_canon` es el resultado del pipeline de limpieza de W09: ya está en `snake_case`, sin espacios, sin mayúsculas. Aplicar `LOWER(TRIM(...))` en runtime es redundante. El `LIKE '%transit%'` con wildcard inicial impide predicado pushdown en Parquet y obliga a evaluar la expresión completa por cada fila. La comparación por igualdad es O(1) vs O(n·m) del LIKE.

**Consecuencia:** speedup 2.69× medido en benchmark (5.6 ms → 2.1 ms).

---

### Decisión 2: `disc_era` precomputada en lugar de `CASE WHEN disc_year_int` en runtime (Q2)

**Contexto:**  
La query baseline recalculaba la era de descubrimiento con una expresión `CASE WHEN disc_year_int < 2000 THEN ...` tanto en el `SELECT` como en el `GROUP BY`, evaluándola dos veces por fila.

**Decisión:**  
Usar la columna `disc_era` que ya existe en `silver_planet_v3` desde W09.

**Justificación:**  
`disc_era` fue creada precisamente para materializar esta lógica. Recalcularla en cada query viola el principio de que el pipeline de limpieza existe para hacer el trabajo de normalización una sola vez. El plan EXPLAIN ANALYZE confirma que el baseline evalúa el CASE en la PROJECTION y de nuevo en el ORDER_BY.

**Consecuencia:** speedup 4.71× medido (6.7 ms → 1.4 ms). El plan optimizado muestra `ORDER_BY disc_era ASC` en lugar de la expresión CASE completa.

---

### Decisión 3: `COUNT(*)` en lugar de `COUNT(DISTINCT pl_name)` (Q2)

**Contexto:**  
El baseline usaba `COUNT(DISTINCT pl_name)` para contar planetas únicos por era.

**Decisión:**  
Usar `COUNT(*)`.

**Justificación:**  
Cada fila de `silver_planet_v3` representa exactamente un planeta (pl_name es el identificador único). No hay duplicados por construcción del dataset. `COUNT(DISTINCT ...)` requiere materializar un hash set de hasta 6 087 valores para luego verificar que ninguno se repite — trabajo completamente innecesario. `COUNT(*)` produce el mismo resultado sin overhead de memoria.

**Consecuencia:** contribuye a la reducción de 59% en Q2 junto con la eliminación del CASE doble.

---

### Decisión 4: gold mart `gold_discovery_summary` para consultas de dashboard

**Contexto:**  
Q2 y variantes similares (filtrar por era + método) se ejecutarán en dashboards con potencialmente cientos de requests por minuto. Incluso después de optimizar, Q2 sobre `silver_planet_v3` sigue haciendo un full scan de 6 087 filas.

**Decisión:**  
Crear `gold_discovery_summary` como tabla pre-agregada con granularidad `(disc_era, discoverymethod_canon)`.

**Justificación:**  
Los datos de eras pasadas (pre-2000, 2000s, 2010s) son estáticos — los planetas históricos no cambian de era. La tabla gold solo necesita reconstruirse cuando llegan datos nuevos. Con 29 filas, cualquier query sobre el gold mart se resuelve en < 1 ms independientemente de la complejidad del filtro, sin tocar la tabla silver de 6 087 filas.

**Consecuencia:** Q2 via gold mart = 0.72 ms, speedup 9.3× vs baseline. La validación confirma que `SUM(n_planets)` en gold == `COUNT(*)` en silver (ex-unknown): 6 086 == 6 086.

**Riesgo:** si se agregan columnas a silver_planet_v3 que el gold no materializa, habrá que reconstruirlo. Documentar como dependencia en el pipeline de ingesta.
