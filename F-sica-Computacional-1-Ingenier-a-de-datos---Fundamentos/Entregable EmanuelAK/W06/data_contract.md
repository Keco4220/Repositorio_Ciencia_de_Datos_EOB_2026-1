# Data Contract — Proyecto Exoplanetas NASA (v1.1.0)

**Dataset:** NASA Exoplanet Archive PSCompPars  
**Version:** 1.1.0 (actualizado en W06 — agrega modelo con llaves)  
**Ultima actualizacion:** 2025-01-24

---

## Capas del pipeline

```
Bronze (raw_ps)  ->  Silver (silver_planet)  ->  dim/fact con llaves  ->  Gold (vistas)
```

---

## Bronze — raw_ps

| Campo | Valor |
|---|---|
| Fuente | data/raw/pscomppars.csv |
| Grain | 1 fila ~ 1 planeta (pl_name) |
| Filas | 6087 |
| Columnas | 16 |
| Regla | No se edita. Inmutable. |

---

## Silver — silver_planet

| Campo | Valor |
|---|---|
| Grain | 1 fila = 1 planeta (pl_name) |
| Filas | 6081 |
| Reglas aplicadas | pl_name NOT NULL, hostname NOT NULL, disc_year [1980-2026], pl_rade (0,30], pl_bmasse > 0 |
| Filas eliminadas | 6 (pl_rade > 30 — objetos subtelares) |

---

## Dimension — dim_host_sk

| Campo | Valor |
|---|---|
| Grain | 1 fila = 1 estrella anfitriona |
| PK | host_id INTEGER (surrogate, generado con ROW_NUMBER) |
| UNIQUE | hostname VARCHAR NOT NULL |
| Filas | 4537 |
| Cardinalidad | n_rows == n_keys == 4537 |
| Columnas | host_id, hostname, sy_dist, ra, dec, st_teff, st_rad, st_mass |

---

## Fact — fact_planet_sk

| Campo | Valor |
|---|---|
| Grain | 1 fila = 1 planeta (pl_name) |
| PK | pl_name VARCHAR |
| FK | host_id -> dim_host_sk(host_id) |
| Filas | 6081 |
| orphan_rows | 0 (integridad referencial verificada) |
| Columnas | pl_name, host_id, discoverymethod, disc_year, pl_orbper, pl_rade, pl_bmasse, pl_eqt |

---

## Gold — vistas

### gold_by_discoverymethod
- Grain: 1 fila por metodo de descubrimiento
- Metricas: n_planets, avg_pl_rade, avg_pl_bmasse, min/max_disc_year
- Exportada en: artifacts/gold_by_discoverymethod.csv

### gold_by_host
- Grain: 1 fila por estrella anfitriona
- JOIN: fact_planet_sk + dim_host_sk por host_id
- Metricas: n_planets, avg_pl_rade, avg_pl_bmasse
- Exportada en: artifacts/gold_by_host.csv

---

## Checks minimos (deben pasar antes de usar Gold)

| Check | Query | Valor esperado |
|---|---|---|
| pk_unique_pl_name | COUNT(*) == COUNT(DISTINCT pl_name) en fact_planet_sk | PASS |
| dim_cardinalidad | COUNT(*) == COUNT(DISTINCT hostname) en dim_host_sk | PASS (4537) |
| orphan_rows | LEFT JOIN + WHERE d.host_id IS NULL | 0 |
| nulls_pl_name | COUNT(*) - COUNT(pl_name) en raw_ps | 0 |
| pl_rade_range | pl_rade > 0 AND pl_rade <= 30 | 6 outliers eliminados en Silver |
