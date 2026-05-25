# W01B — Sanity Checks sobre Raw (datos reales NASA)

**Archivo:** `data/raw/pscomppars.csv`  
**Tamaño:** 930,507 bytes  
**SHA-256:** `d89390c3ccfcced5e13815e9b5025057774ac0c0b958e1cab434ca97252531b3`

---

## Check 1 — Filas y columnas

```sql
SELECT COUNT(*) FROM raw_ps;
-- n_rows = 6087

SELECT COUNT(*) FROM pragma_table_info('raw_ps');
-- n_cols = 16
```

**Resultado:** `n_rows = 6087`, `n_cols = 16`

✅ Dataset completo del catálogo NASA PSCompPars con las 16 columnas estándar.

---

## Check 2 — Nulos en columna clave `pl_name`

```sql
SELECT COUNT(*) AS null_pl_name FROM raw_ps WHERE pl_name IS NULL;
```

**Resultado:** `0`

✅ Todos los planetas tienen nombre. La clave primaria está completa.

---

## Check 3 — Muestra de 10 filas reales

```sql
SELECT pl_name, hostname, discoverymethod, disc_year
FROM raw_ps
WHERE pl_name IS NOT NULL
LIMIT 10;
```

**Resultado:**
| pl_name | hostname | discoverymethod | disc_year |
|---|---|---|---|
| Kepler-1167 b | Kepler-1167 | Transit | 2016 |
| Kepler-1740 b | Kepler-1740 | Transit | 2021 |
| Kepler-1581 b | Kepler-1581 | Transit | 2016 |
| Kepler-644 b | Kepler-644 | Transit | 2016 |
| Kepler-1752 b | Kepler-1752 | Transit | 2021 |
| Kepler-280 c | Kepler-280 | Transit | 2014 |
| Kepler-1208 b | Kepler-1208 | Transit | 2016 |
| Kepler-263 c | Kepler-263 | Transit | 2014 |
| Kepler-1101 b | Kepler-1101 | Transit | 2016 |
| HD 168746 b | HD 168746 | Radial Velocity | 2002 |

✅ Datos reales del catálogo NASA con estructura correcta.

---

## Check 4 (EXTRA — Tarea) — Duplicados por `pl_name`

```sql
SELECT COUNT(*) AS dup_count FROM (
    SELECT pl_name, COUNT(*) AS cnt
    FROM raw_ps
    GROUP BY pl_name
    HAVING cnt > 1
);
```

**Resultado:** `0` — no hay duplicados en `pl_name`.

✅ Cada planeta tiene exactamente una entrada. El identificador primario es consistente.

**Hallazgo adicional:** Se detectaron **8 planetas con `disc_year = 2026`** (TOI-5422 b, KMT-2022-BLG-1818L b/c, TOI-5789 b/d/e, TOI-5349 b, HIP 54515 b). Esto corresponde a publicaciones adelantadas en el catálogo NASA, no a errores de datos. Decisión documentada en `decisions_log.md`.

---

## Nulos por columna (resumen de calidad)

| Columna | Nulos | % de 6087 |
|---|---|---|
| pl_eqt | 1539 | 25.3% |
| pl_orbper | 321 | 5.3% |
| st_rad | 302 | 5.0% |
| st_teff | 280 | 4.6% |
| pl_rade | 50 | 0.8% |
| pl_bmasse | 31 | 0.5% |
| sy_dist | 27 | 0.4% |
| st_mass | 7 | 0.1% |
| disc_year | 1 | 0.02% |

⚠️ `pl_eqt` tiene alta tasa de nulos (25%). A considerar en Silver para imputación o filtrado.

---

## Distribución por método de descubrimiento

| Método | Planetas |
|---|---|
| Transit | 4488 |
| Radial Velocity | 1161 |
| Microlensing | 265 |
| Imaging | 91 |
| Transit Timing Variations | 39 |
| Otros | 43 |

---

## Reflexión (DDIA Cap.1)

**¿Qué haría al sistema "no confiable" aunque el código corra?**
- Que NASA actualice el CSV silenciosamente (nueva versión con mismo nombre) → por eso guardamos SHA-256.
- Que `pl_name` tenga duplicados → conteos de planetas serían incorrectos.
- Que los 8 planetas con `disc_year=2026` sean tratados como errores sin investigar → pérdida de datos válidos.
- Que los 1539 nulos en `pl_eqt` sean ignorados → modelos de temperatura serían sesgados.

**¿Qué documento quisieras encontrar si heredas el proyecto?**
- Un `decisions_log.md` que explique *por qué* se conservaron los `disc_year=2026`.
- Un `glossary.md` con el significado físico de cada columna.
- Un `runbook` con pasos exactos para descargar el CSV desde la API NASA.
