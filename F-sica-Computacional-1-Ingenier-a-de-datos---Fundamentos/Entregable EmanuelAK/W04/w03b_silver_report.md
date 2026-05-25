# W04B — Reporte Silver: construccion de capas

---

## DESCRIBE silver_planet

| columna | tipo | regla aplicada |
|---|---|---|
| pl_name | VARCHAR | NOT NULL (clave) |
| hostname | VARCHAR | NOT NULL (clave FK) |
| discoverymethod | VARCHAR | — |
| disc_year | BIGINT | [1980, 2026] si not null |
| sy_snum | BIGINT | — |
| sy_pnum | BIGINT | — |
| sy_dist | DOUBLE | — |
| ra | DOUBLE | — |
| dec | DOUBLE | — |
| pl_orbper | DOUBLE | > 0 si not null (regla extra) |
| pl_rade | DOUBLE | (0, 30] si not null |
| pl_bmasse | DOUBLE | > 0 si not null |
| pl_eqt | DOUBLE | — |
| st_teff | DOUBLE | — |
| st_rad | DOUBLE | — |
| st_mass | DOUBLE | — |

## Conteos silver_planet

| metrica | valor |
|---|---|
| n_rows | 6081 |
| distinct pl_name | 6081 |
| distinct hostname | 4537 |
| filas eliminadas de raw | 6 |

Motivo de eliminacion: 6 planetas con `pl_rade > 30` (objetos subtelares). Ninguna fila fue eliminada por pl_name/hostname nulos ni disc_year fuera de rango.

---

## dim_host_full

```sql
CREATE TABLE dim_host_full AS
SELECT hostname, MAX(sy_dist), MAX(ra), MAX(dec), MAX(st_teff), MAX(st_rad), MAX(st_mass)
FROM silver_planet
WHERE hostname IS NOT NULL
GROUP BY hostname
```

| metrica | valor |
|---|---|
| n_rows | 4537 |
| n_keys (DISTINCT hostname) | 4537 |
| n_rows == n_keys | SI ✅ |

La cardinalidad 1:1 esta garantizada. El JOIN con fact_planet es seguro.

---

## fact_planet

```sql
CREATE TABLE fact_planet AS
SELECT DISTINCT pl_name, hostname, discoverymethod, disc_year,
       pl_orbper, pl_rade, pl_bmasse, pl_eqt
FROM silver_planet WHERE pl_name IS NOT NULL
```

| metrica | valor |
|---|---|
| n_rows | 6081 |
| distinct pl_name | 6081 |

## Validacion JOIN sano

```sql
SELECT COUNT(*) FROM fact_planet f
JOIN dim_host_full h ON f.hostname = h.hostname
```

| n_fact | n_join | resultado |
|---|---|---|
| 6081 | 6081 | SIN duplicacion ✅ |

---

## Vistas Gold

### gold_by_method

| discoverymethod | n_planets | avg_rade | median_orbper |
|---|---|---|---|
| Transit | 4487 | 4.3651 | 8.16 dias |
| Radial Velocity | 1161 | 9.7915 | 305.5 dias |
| Microlensing | 265 | 9.860 | 3142.5 dias |
| Imaging | 86 | 13.446 | 32000.0 dias |
| Transit Timing Variations | 39 | 6.4934 | 30.0 dias |

### gold_by_host (top 5)

| hostname | n_planets | avg_rade |
|---|---|---|
| KOI-351 | 8 | 3.900 |
| TRAPPIST-1 | 7 | 0.979 |
| HD 10180 | 6 | 6.677 |
| Kepler-11 | 6 | 2.967 |
| HD 219134 | 6 | 3.669 |
