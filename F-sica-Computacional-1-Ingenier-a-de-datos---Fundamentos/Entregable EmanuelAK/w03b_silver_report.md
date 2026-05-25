# W03B Silver Report

## DESCRIBE silver_planet

| column_name     | column_type |
|-----------------|-------------|
| pl_name         | VARCHAR     |
| hostname        | VARCHAR     |
| discoverymethod | VARCHAR     |
| disc_year       | BIGINT      |
| sy_snum         | BIGINT      |
| sy_pnum         | BIGINT      |
| sy_dist         | DOUBLE      |
| ra              | DOUBLE      |
| dec             | DOUBLE      |
| pl_orbper       | DOUBLE      |
| pl_rade         | DOUBLE      |
| pl_bmasse       | DOUBLE      |
| pl_eqt          | DOUBLE      |
| st_teff         | DOUBLE      |
| st_rad          | DOUBLE      |
| st_mass         | DOUBLE      |

## Counts

- n_rows: 6101
- n_pl (distinct pl_name): 6101

## dim_host_full

- n_rows: 4554
- n_keys (distinct hostname): 4554

## JOIN sano

- n_fact: 6101
- n_join: 6101 (SELECT COUNT(*) FROM fact_planet f JOIN dim_host_full d ON f.hostname = d.hostname)

El JOIN es sano porque n_join = n_fact, sin inflar filas.