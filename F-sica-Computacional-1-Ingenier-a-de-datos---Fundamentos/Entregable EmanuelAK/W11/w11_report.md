# W11 Report — Query Optimization + Gold Mart

**Fecha:** 2026-05-19  
**Dataset:** `silver_planet_v3` (6 087 planetas — NASA Exoplanet Archive)

---

## 1. Queries críticas del proyecto

| ID | Descripción | Caso de uso |
|---|---|---|
| Q1 | Estrellas con ≥2 planetas descubiertos por tránsito | Dashboard de sistemas multi-planeta |
| Q2 | Estadísticas de planetas por era de descubrimiento | Panel de tendencias históricas |

---

## 2. Performance budget

| Query | Budget objetivo | Justificación |
|---|---|---|
| Q1 | **< 5 ms** | Consulta interactiva en UI; latencia > 100 ms es perceptible para el usuario |
| Q2 | **< 3 ms** | Agregación simple pre-computable; con gold mart puede ser sub-ms |

---

## 3. Baseline con tiempos

Medido con 5 ejecuciones, promedio y mínimo:

| Query | avg (ms) | min (ms) | Budget | Estado |
|---|---|---|---|---|
| Q1 BASELINE | 5.594 | 3.090 | < 5 ms | ✗ FALLA (avg supera budget) |
| Q2 BASELINE | 6.728 | 2.874 | < 3 ms | ✗ FALLA (avg supera budget) |

---

## 4. EXPLAIN ANALYZE

Ver archivos:
- `docs/w11_explain_analyze_baseline.txt`
- `docs/w11_explain_analyze_optimized.txt`

**Observaciones clave del plan baseline:**

- **Q1:** `TABLE_SCAN → 6 087 rows` con filtro `lower(trim(discoverymethod_canon)) LIKE '%transit%'` aplicado fila a fila. El wildcard inicial (`%transit`) impide cualquier optimización de predicado.
- **Q2:** `TABLE_SCAN → 6 087 rows` con expresión `CASE WHEN disc_year_int < ...` evaluada **dos veces** (en `SELECT` y en `GROUP BY`). `COUNT(DISTINCT pl_name)` materializa un hash set completo.

---

## 5. Anti-patrones identificados

### Anti-patrón 1 — Funciones sobre columnas ya normalizadas en el `WHERE` (Q1)

```sql
-- MALO
WHERE LOWER(TRIM(discoverymethod_canon)) LIKE '%transit%'

-- discoverymethod_canon ya es 'transit' (snake_case, sin espacios)
-- LOWER(TRIM(...)) se evalúa 6087 veces en runtime — trabajo innecesario
-- LIKE '%transit%' con wildcard inicial bloquea row-group pruning en Parquet
```

**Impacto:** CPU desperdiciada en cada fila. En datasets de millones de filas, esto puede suponer segundos de diferencia.

---

### Anti-patrón 2 — Subquery `SELECT *` innecesaria (Q1)

```sql
-- MALO
FROM (SELECT * FROM silver_planet_v3 WHERE ...) sub
GROUP BY LOWER(TRIM(hostname_canon))

-- SELECT * proyecta 18 columnas para luego usar solo 4
-- LOWER(TRIM(hostname_canon)) re-normaliza una columna ya limpia
```

**Impacto:** proyección innecesaria de columnas + función redundante en GROUP BY.

---

### Anti-patrón 3 — Expresión `CASE WHEN` duplicada en `SELECT` y `GROUP BY` (Q2)

```sql
-- MALO
SELECT CASE WHEN disc_year_int < 2000 THEN 'pre-2000' ... END AS era_recomputed
GROUP BY CASE WHEN disc_year_int < 2000 THEN 'pre-2000' ... END

-- disc_era ya existe en silver_planet_v3 con exactamente esta lógica
-- El CASE se evalúa dos veces por fila = 2 × 6087 evaluaciones
```

**Impacto:** CPU duplicada. `disc_era` fue producida precisamente para evitar este recálculo.

---

### Anti-patrón 4 — `COUNT(DISTINCT pl_name)` donde `pl_name` es único (Q2)

```sql
-- MALO
COUNT(DISTINCT pl_name)

-- pl_name identifica de forma única a cada planeta (una fila = un planeta)
-- COUNT(DISTINCT ...) mantiene un hash set para deduplicar — overhead innecesario
-- COUNT(*) da el mismo resultado sin el hash set
```

**Impacto:** asignación de memoria para hash set que nunca encontrará duplicados.

---

## 6. Reescrituras justificadas

### Q1 — Reescritura

```sql
-- ANTES (baseline)
SELECT LOWER(TRIM(hostname_canon)) AS host, COUNT(*) ...
FROM ( SELECT * FROM silver_planet_v3
       WHERE LOWER(TRIM(discoverymethod_canon)) LIKE '%transit%' ... ) sub
GROUP BY LOWER(TRIM(hostname_canon))

-- DESPUÉS (optimizado)
SELECT hostname_canon AS host, COUNT(*) ...
FROM silver_planet_v3
WHERE discoverymethod_canon = 'transit'
  AND pl_rade IS NOT NULL AND pl_bmasse IS NOT NULL
GROUP BY hostname_canon
```

**Cambios:** eliminada subquery, `LIKE '%transit%'` → `= 'transit'`, funciones redundantes en GROUP BY eliminadas.

### Q2 — Reescritura

```sql
-- ANTES (baseline)
SELECT CASE WHEN disc_year_int < 2000 THEN ... END AS era_recomputed,
       COUNT(DISTINCT pl_name), AVG(CASE WHEN pl_eqt IS NOT NULL THEN pl_eqt END)
FROM silver_planet_v3 WHERE disc_year_int IS NOT NULL
GROUP BY CASE WHEN disc_year_int < 2000 THEN ... END

-- DESPUÉS (optimizado)
SELECT disc_era, COUNT(*), ROUND(AVG(pl_eqt), 2), ROUND(AVG(sy_dist), 2)
FROM silver_planet_v3
WHERE disc_era != 'unknown'
GROUP BY disc_era
```

**Cambios:** `disc_era` precalculada en lugar de CASE en SELECT+GROUP BY, `COUNT(*)` en lugar de `COUNT(DISTINCT pl_name)`, `AVG(col)` nativo elimina el CASE redundante.

---

## 7. Gold mart: `gold_discovery_summary`

**Esquema:** `(disc_era, discoverymethod_canon)` × métricas

```sql
CREATE TABLE gold_discovery_summary AS
SELECT
    disc_era, discoverymethod_canon,
    COUNT(*)                        AS n_planets,
    COUNT(DISTINCT hostname_canon)  AS n_host_stars,
    ROUND(AVG(pl_rade),   4)        AS avg_radius_earth,
    ROUND(AVG(pl_bmasse), 4)        AS avg_mass_earth,
    ROUND(AVG(pl_eqt),    2)        AS avg_temp_k,
    ROUND(AVG(sy_dist),   2)        AS avg_dist_pc,
    ROUND(MIN(sy_dist),   2)        AS min_dist_pc,
    ROUND(MAX(sy_dist),   2)        AS max_dist_pc,
    ROUND(AVG(st_teff),   2)        AS avg_star_teff
FROM silver_planet_v3
WHERE disc_era != 'unknown'
GROUP BY disc_era, discoverymethod_canon
```

**Resultado:** 29 filas (4 eras × hasta 11 métodos, según disponibilidad)

**Top 5 combinaciones por número de planetas:**

| disc_era | método | n_planets | n_host_stars | avg_dist_pc |
|---|---|---|---|---|
| 2010s | transit | 3 064 | 2 610 | 689.57 |
| 2020s | transit | 1 362 | 1 215 | 402.23 |
| 2010s | radial_velocity | 456 | 449 | 109.03 |
| 2020s | radial_velocity | 389 | 383 | 74.47 |
| 2000s | radial_velocity | 289 | 284 | 65.97 |

---

## 8. Validación de resultados

| Check | Resultado |
|---|---|
| `SUM(n_planets)` en gold == `COUNT(*)` en silver (ex-unknown) | ✅ 6 086 == 6 086 |
| Eras cubiertas en gold | ✅ 4 (pre-2000, 2000s, 2010s, 2020s) |
| Métodos cubiertos en gold | ✅ 10 de 11 (disk_kinematics no tiene era válida) |
| Combinaciones en gold | ✅ 29 filas |

---

## 9. Comparación antes/después

Medición con 5 runs, promedio:

| Query | Baseline (ms) | Optimized (ms) | Speedup | Budget | Estado |
|---|---|---|---|---|---|
| Q1 — multi-planet hosts | 5.594 | 2.082 | **2.69×** | < 5 ms | ✅ PASS |
| Q2 — era stats | 6.728 | 1.429 | **4.71×** | < 3 ms | ✅ PASS |
| Q2 — via gold mart | 6.728 | 0.723 | **9.31×** | < 3 ms | ✅ PASS |

Ambas queries pasan el budget después de la optimización. El gold mart lleva Q2 a sub-ms.

---

## 10. Decisión técnica final

**Q1:** usar la versión optimizada con `= 'transit'` y sin subquery. Speedup 2.69× con margen holgado sobre el budget de 5 ms.

**Q2:** usar `gold_discovery_summary` para el dashboard de tendencias. 29 filas pre-agregadas responden en 0.7 ms — 9× más rápido que el baseline. La tabla se refresca con un único `INSERT OVERWRITE` tras cada ingesta de datos nuevos.

**Regla general:**
> No aplicar funciones de normalización sobre columnas que el pipeline de limpieza ya normalizó. No recalcular en runtime lo que se puede calcular una vez en batch.
