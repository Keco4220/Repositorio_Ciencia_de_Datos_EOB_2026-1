# Decisions Log

---

## W08 — 2026-05-19

### Decisión 1: Canonicalización de `discoverymethod` con `method_map` + `COALESCE`

**Contexto:**  
La columna `discoverymethod` en el dataset raw de la NASA tiene 11 valores únicos con formato inconsistente (mayúsculas, espacios, palabras compuestas). Se necesitaba una forma canónica para análisis posteriores.

**Decisión:**  
Crear una tabla de lookup `method_map(raw_method, canonical_method)` con mapeo explícito raw → `snake_case`, y unirla al silver mediante `LEFT JOIN + COALESCE`. Si llega un método nuevo sin mapeo, el fallback es `LOWER(TRIM(discoverymethod))`, lo que evita pérdida de filas.

**Alternativas descartadas:**  
- `REPLACE`/`REGEXP_REPLACE` directo en SQL: frágil ante variaciones tipográficas futuras.  
- `CASE WHEN` inline en el `SELECT`: difícil de mantener y escalar si se agregan métodos.

**Consecuencias:**  
- 0 filas perdidas en raw → silver.  
- La tabla `method_map` es el único punto de mantenimiento si cambia la nomenclatura upstream.  
- El `COALESCE` actúa como red de seguridad ante métodos desconocidos.

---

### Decisión 2: Modelado M:N con link table y PK compuesta

**Contexto:**  
Un planeta puede ser detectado por múltiples métodos y un método puede detectar múltiples planetas. Modelar esto en una sola tabla con columnas repetidas violaría la 1NF.

**Decisión:**  
Usar una **link table** (`planet_method_demo`) con PK compuesta `(planet_id, method_id)` y FK explícitas hacia `planet_demo` y `method_demo`. Esto es el patrón estándar para relaciones M:N en SQL relacional.

**Alternativas descartadas:**  
- Columna `methods` como lista separada por comas en `planet_demo`: no es normalizable, impide joins eficientes y viola 1NF.  
- Dos columnas `method_1`, `method_2` en `planet_demo`: no escala y genera muchos NULLs.

**Consecuencias:**  
- La PK compuesta bloquea duplicados por diseño (verificado con `HAVING COUNT(*) > 1` → 0 filas y prueba de inserción duplicada).  
- Las FK garantizan integridad referencial: no se pueden insertar relaciones con planetas o métodos inexistentes.  
- Queries de agregación (planetas por método, métodos por planeta) son directas con `COUNT(DISTINCT ...)` sobre la link table.
