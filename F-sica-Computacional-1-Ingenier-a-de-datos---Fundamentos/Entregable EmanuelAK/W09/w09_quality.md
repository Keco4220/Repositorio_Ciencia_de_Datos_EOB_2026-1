# W09 Quality Gates — Resultados de Ejecución

**Fecha de ejecución:** 2026-05-19  
**Tabla auditada:** `silver_planet_v3`  
**Fuente raw:** `pscomppars.csv` (6 087 registros)

---

## Resumen ejecutivo

| check_name | status | metric_value | details |
|---|---|---|---|
| `disc_year_bad_rate` | ✅ PASS | 0.000164 | 1 bad disc_year de 6 087 (0.0164%) |
| `null_discoverymethod_canon` | ✅ PASS | 0.0 | 0 nulls en discoverymethod_canon |
| `null_hostname_canon` | ✅ PASS | 0.0 | 0 nulls en hostname_canon |
| `row_count_parity` | ✅ PASS | 6087.0 | raw=6 087, silver=6 087 |

**Estado global: 4/4 PASS — pipeline saludable ✓**

---

## Detalle por check

### 1. `row_count_parity`
- **Qué mide:** que no se pierdan ni se dupliquen filas en el paso raw → silver.
- **Cómo:** `COUNT(*) silver_planet_v3 == COUNT(*) raw_ps`.
- **Umbral:** igualdad exacta.
- **Resultado:** 6 087 == 6 087 → **PASS**.
- **Riesgo si falla:** pérdida de datos en el pipeline de limpieza (JOIN mal configurado, filtro accidental).

### 2. `null_hostname_canon`
- **Qué mide:** integridad de la clave de agrupación por estrella huésped.
- **Cómo:** `COUNT(*) WHERE hostname_canon IS NULL`.
- **Umbral:** = 0 (ningún planeta puede quedar sin estrella).
- **Resultado:** 0 nulls → **PASS**.
- **Riesgo si falla:** planetas huérfanos que rompen joins downstream con tablas de estrellas.

### 3. `disc_year_bad_rate`
- **Qué mide:** tasa de registros con `disc_year` no parseable como entero.
- **Cómo:** `n_bad / n_total` donde `n_bad = COUNT(*) WHERE disc_year_bad`.
- **Umbral:** < 1% (tolerancia para datos ausentes en la fuente).
- **Resultado:** 1 / 6 087 = 0.0164% → **PASS**.
- **Nota:** el único registro malo corresponde a `disc_year = NULL` en el raw, no a un valor corrupto.

### 4. `null_discoverymethod_canon`
- **Qué mide:** cobertura completa del mapeo de métodos de detección.
- **Cómo:** `COUNT(*) WHERE discoverymethod_canon IS NULL`.
- **Umbral:** = 0 (el COALESCE debe capturar cualquier método no mapeado).
- **Resultado:** 0 nulls → **PASS**.
- **Riesgo si falla:** métodos desconocidos que podrían indicar un cambio en la nomenclatura de la fuente upstream (NASA Exoplanet Archive).

---

## Notas de mantenimiento

- Si la NASA agrega un nuevo `discoverymethod` al dataset, el check `null_discoverymethod_canon` seguirá siendo **PASS** gracias al `COALESCE` fallback (`LOWER(TRIM(...))`), pero el valor no tendrá un canónico explícito. Se recomienda revisar periódicamente con:

```sql
SELECT discoverymethod_canon, COUNT(*) AS n
FROM silver_planet_v3
WHERE discoverymethod_canon NOT IN (SELECT canonical FROM method_synonyms)
GROUP BY discoverymethod_canon;
```

- El umbral del 1% para `disc_year_bad_rate` puede ajustarse si el dataset raw cambia de estructura. Documentar cualquier cambio en `decisions_log.md`.
