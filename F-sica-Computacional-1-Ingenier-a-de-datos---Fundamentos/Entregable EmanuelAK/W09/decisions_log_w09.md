# Decisions Log

---

## W09 — 2026-05-19

### Decisión 1: `method_synonyms` con join por `raw_norm` en lugar de join por valor literal

**Contexto:**  
En W08 se usó `method_map` con join directo sobre el valor literal de `discoverymethod` (ej. `"Transit"`). Esto funciona si el raw es estable, pero falla si hay variaciones de capitalización (`"transit"`, `"TRANSIT"`) o espacios adicionales.

**Decisión:**  
Crear `method_synonyms` donde `raw_norm = LOWER(TRIM(discoverymethod))` y hacer el join `ON LOWER(TRIM(raw_ps.discoverymethod)) = ms.raw_norm`. Así el mapeo es robusto ante variaciones tipográficas sin necesidad de enumerar cada variante.

**Alternativas descartadas:**  
- Join por valor literal (W08): frágil ante capitalización inconsistente.  
- `ILIKE` en el join: no es idempotente y puede generar matches falsos positivos.

**Consecuencias:**  
- 0 nulls en `discoverymethod_canon` (check `null_discoverymethod_canon` = PASS).  
- El mapeo sigue siendo un único punto de mantenimiento en `method_synonyms`.

---

### Decisión 2: `TRY_CAST` + flag `disc_year_bad` en lugar de `CAST` directo

**Contexto:**  
`disc_year` en el raw es de tipo `BIGINT` (ya parseado por DuckDB), pero puede contener NULLs. Se necesitaba una columna `disc_year_int` limpia y un mecanismo para detectar anomalías sin abortar el pipeline.

**Decisión:**  
Usar `TRY_CAST(disc_year AS INTEGER)` que retorna NULL en lugar de error para valores no convertibles, y agregar un flag booleano `disc_year_bad = (TRY_CAST(...) IS NULL)` para hacer las anomalías auditables en el quality gate.

**Alternativas descartadas:**  
- `CAST` directo: lanza excepción y aborta el `CREATE TABLE AS SELECT` si hay un valor inválido.  
- Filtrar filas con `disc_year IS NULL` antes del cast: pierde datos y rompe la paridad de filas.

**Consecuencias:**  
- `row_count_parity` PASS: 0 filas perdidas por el cast.  
- El registro con `disc_year = NULL` queda en silver con `disc_year_bad = true` y `disc_era = 'unknown'`, auditable y sin impacto en el resto del pipeline.

---

### Decisión 3: `quality_events` como tabla persistente con timestamp

**Contexto:**  
Los checks de calidad se hacían de forma ad-hoc con `SELECT COUNT(*)` en celdas sueltas del notebook. Esto no deja trazabilidad entre ejecuciones.

**Decisión:**  
Crear la tabla `quality_events(ts_utc, check_name, status, metric_value, details)` donde cada ejecución inserta 4 filas con timestamp UTC. Los umbrales se computan dinámicamente en Python antes del INSERT.

**Alternativas descartadas:**  
- Checks solo en el notebook sin persistencia: no auditables, no comparables entre ejecuciones.  
- Una sola fila resumen por ejecución: pierde granularidad por check.

**Consecuencias:**  
- 4/4 PASS en la ejecución del 2026-05-19.  
- La tabla acumula historial entre ejecuciones, lo que permite detectar regresiones con `SELECT * FROM quality_events WHERE status = 'FAIL' ORDER BY ts_utc DESC`.  
- El umbral de `disc_year_bad_rate` (< 1%) está documentado en el código y en `w09_quality.md` para facilitar su revisión futura.
