# W09 Report — Limpieza Avanzada + Quality Gates

**Fecha:** 2026-05-19  
**Dataset:** `pscomppars.csv` (NASA Exoplanet Archive — 6 087 registros)

---

## Parte A — Limpieza avanzada

### TODO 1 — `method_synonyms`

Se creó la tabla `method_synonyms(raw_norm, canonical)` donde `raw_norm` es el valor normalizado con `LOWER(TRIM(...))` y `canonical` es la forma definitiva en `snake_case`.

La diferencia con `method_map` de W08 es que el join ahora se hace sobre la forma **ya normalizada**, lo que hace el mapeo robusto ante variaciones de capitalización sin depender del valor literal del raw.

| raw_norm | canonical |
|---|---|
| transit | transit |
| radial velocity | radial_velocity |
| imaging | imaging |
| microlensing | microlensing |
| pulsar timing | pulsar_timing |
| transit timing variations | transit_timing_variations |
| eclipse timing variations | eclipse_timing_variations |
| orbital brightness modulation | orbital_brightness_modulation |
| astrometry | astrometry |
| pulsation timing variations | pulsation_timing_variations |
| disk kinematics | disk_kinematics |

Total: **11 sinónimos** — cubre el 100% de los métodos presentes en el dataset.

---

### TODO 2 — `silver_planet_v3`

**Transformaciones aplicadas:**

| Columna nueva | Lógica |
|---|---|
| `hostname_canon` | `LOWER(TRIM(hostname))` |
| `discoverymethod_canon` | `COALESCE(ms.canonical, LOWER(TRIM(discoverymethod)))` — join por `raw_norm` |
| `disc_year_int` | `TRY_CAST(disc_year AS INTEGER)` — retorna NULL si falla en lugar de error |
| `disc_year_bad` | `(TRY_CAST(disc_year AS INTEGER) IS NULL)` — flag booleano |
| `disc_era` | `CASE` por rango de `disc_year_int` |

**Checks de calidad tras construcción:**

| Métrica | Resultado |
|---|---|
| Filas raw | 6 087 |
| Filas silver_planet_v3 | 6 087 |
| Pérdida de filas | **0** |
| `hostname_canon` nulos | **0** |
| `discoverymethod_canon` nulos | **0** |
| `disc_year_bad` (NULL tras cast) | **1** (0.02%) |

**Distribución `disc_era`:**

| disc_era | n |
|---|---|
| pre-2000 | 30 |
| 2000s | 380 |
| 2010s | 3 683 |
| 2020s | 1 993 |
| unknown | 1 |

El único `unknown` corresponde al registro con `disc_year = NULL` en el dataset raw (verificado). No representa un problema de limpieza sino un dato ausente en la fuente.

**Distribución `discoverymethod_canon` (top 5):**

| método | n |
|---|---|
| transit | 4 488 |
| radial_velocity | 1 161 |
| microlensing | 265 |
| imaging | 91 |
| transit_timing_variations | 39 |

---

## Parte B — Quality Gates

### Diseño de `quality_events`

```sql
CREATE TABLE quality_events(
    ts_utc        TIMESTAMP,
    check_name    VARCHAR,
    status        VARCHAR,   -- 'PASS' | 'FAIL'
    metric_value  DOUBLE,
    details       VARCHAR
);
```

### Los 4 checks implementados

| check_name | lógica | umbral | status | metric_value |
|---|---|---|---|---|
| `row_count_parity` | `COUNT(*) silver == COUNT(*) raw` | igualdad exacta | **PASS** | 6 087 |
| `null_hostname_canon` | `COUNT(*) WHERE hostname_canon IS NULL` | = 0 | **PASS** | 0 |
| `disc_year_bad_rate` | `n_bad / n_total` | < 1% | **PASS** | 0.0164% |
| `null_discoverymethod_canon` | `COUNT(*) WHERE discoverymethod_canon IS NULL` | = 0 | **PASS** | 0 |

**Resultado global: 4/4 PASS ✓**

---

## Conclusiones

- `silver_planet_v3` mejora `silver_planet_v2` al hacer el join de métodos sobre la forma normalizada (`LOWER(TRIM(...))`), lo que lo hace más robusto ante variaciones tipográficas.
- `TRY_CAST` es preferible a `CAST` para produccción: permite detectar anomalías sin abortar el pipeline; el flag `disc_year_bad` las hace auditables.
- Los quality gates automatizados convierten los checks manuales del reporte en datos persistentes consultables, lo que permite comparar entre ejecuciones y detectar regresiones.
