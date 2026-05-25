# W04A — Reporte de Calidad: Bronze (raw_ps)

**Dataset:** `data/raw/pscomppars.csv` — 6087 filas, 16 columnas

---

## DEMO — Checks básicos del docente

| Check | Resultado | Estado |
|---|---|---|
| `nulls_pl_name` | 0 | PASS ✅ |
| `nulls_hostname` | 0 | PASS ✅ |
| Duplicados en `pl_name` | 0 filas | PASS ✅ |
| `disc_year` fuera de [1980, 2026] | 0 | PASS ✅ |

---

## TU TURNO 1 — Nulos en 12 columnas

Columnas seleccionadas: las 12 más relevantes para análisis (4 identificadoras + 4 métricas planetarias + 4 del sistema).

```sql
SELECT 'pl_orbper' AS col, COUNT(*) - COUNT(pl_orbper) AS nulls FROM raw_ps
UNION ALL SELECT 'pl_rade',   COUNT(*) - COUNT(pl_rade)   FROM raw_ps
UNION ALL SELECT 'pl_bmasse', COUNT(*) - COUNT(pl_bmasse) FROM raw_ps
UNION ALL SELECT 'sy_dist',   COUNT(*) - COUNT(sy_dist)   FROM raw_ps
UNION ALL SELECT 'disc_year', COUNT(*) - COUNT(disc_year) FROM raw_ps
UNION ALL SELECT 'pl_name',   COUNT(*) - COUNT(pl_name)   FROM raw_ps
UNION ALL SELECT 'hostname',  COUNT(*) - COUNT(hostname)  FROM raw_ps
-- ... (12 columnas en total)
ORDER BY nulls DESC
```

| columna | nulls | % de 6087 |
|---|---|---|
| `pl_orbper` | 321 | 5.27% |
| `pl_rade` | 50 | 0.82% |
| `pl_bmasse` | 31 | 0.51% |
| `sy_dist` | 27 | 0.44% |
| `disc_year` | 1 | 0.02% |
| `pl_name` | 0 | 0.00% |
| `hostname` | 0 | 0.00% |
| `discoverymethod` | 0 | 0.00% |
| `ra` | 0 | 0.00% |
| `dec` | 0 | 0.00% |
| `sy_snum` | 0 | 0.00% |
| `sy_pnum` | 0 | 0.00% |

**Decisión sobre las columnas elegidas:** se priorizaron las columnas de identificación (`pl_name`, `hostname`, `discoverymethod`) que son clave para JOINs, las métricas planetarias principales (`pl_orbper`, `pl_rade`, `pl_bmasse`) que serán usadas en Gold, y las del sistema (`sy_dist`, `ra`, `dec`, `sy_snum`, `sy_pnum`) que contextualizan cada detección.

---

## TU TURNO 2 — Check de rango: pl_rade en (0, 30]

```sql
SELECT COUNT(*) AS n_bad_pl_rade
FROM raw_ps
WHERE pl_rade IS NOT NULL
  AND (pl_rade <= 0 OR pl_rade > 30)
```

**Resultado: `n_bad_pl_rade = 6`** ⚠️

| pl_name | pl_rade (R🜨) |
|---|---|
| V2376 Ori b | 87.21 |
| HD 100546 b | 77.34 |
| GQ Lup b | 33.60 |
| Kepler-297 d | 32.60 |
| PDS 70 b | 30.49 |
| DH Tau b | 30.26 |

**Interpretación:** Estos 6 objetos superan el límite didáctico de 30 R🜨. No son planetas en el sentido convencional — son **compañeros de masa sub-estelar** detectados por Imaging directo (enanas marrones candidatas). El catálogo NASA los incluye porque orbitan estrellas y cumplen criterios de masa planetaria. Para análisis de planetas convencionales, se eliminan en Silver. Para análisis de objetos subtelares, habría que conservarlos — esta decisión está documentada en `decisions_log.md`.

---

## TU TURNO 3 (tarea) — quality_w04a materializado

```sql
CREATE TABLE quality_w04a AS
SELECT run_ts, 'nulls_pl_name'      AS check_name, COUNT(*)-COUNT(pl_name)::BIGINT AS metric_value FROM raw_ps
UNION ALL
SELECT run_ts, 'nulls_hostname',     COUNT(*)-COUNT(hostname)::BIGINT FROM raw_ps
UNION ALL
SELECT run_ts, 'pl_rade_out_range',  COUNT(*)::BIGINT FROM raw_ps WHERE pl_rade IS NOT NULL AND (pl_rade<=0 OR pl_rade>30)
```

| run_ts | check_name | metric_value | status |
|---|---|---|---|
| 2025-01-24T... | nulls_pl_name | 0 | PASS ✅ |
| 2025-01-24T... | nulls_hostname | 0 | PASS ✅ |
| 2025-01-24T... | pl_rade_out_of_range | 6 | WARN ⚠️ |

Exportado a `artifacts/quality_w04a.csv`.

**Explicacion del query:** Cada `SELECT` calcula una metrica distinta (nulos o conteo de fuera de rango) y todas se unen con `UNION ALL` para formar una tabla vertical de checks. Esto permite agregar checks nuevos simplemente añadiendo un `UNION ALL` más, sin cambiar la estructura de la tabla.
