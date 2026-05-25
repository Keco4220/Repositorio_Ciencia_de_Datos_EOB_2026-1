# W03A Quality Report

## Output de TU TURNO 1 (nulos en 12 columnas)

```
┌─────────────────┬───────┐
│       col       │ nulls │
│     varchar     │ int64 │
├─────────────────┼───────┤
│ pl_orbper       │   323 │
│ pl_rade         │    50 │
│ pl_bmasse       │    31 │
│ sy_dist         │    27 │
│ disc_year       │     1 │
│ dec             │     0 │
│ discoverymethod │     0 │
│ hostname        │     0 │
│ pl_name         │     0 │
│ ra              │     0 │
│ sy_pnum         │     0 │
│ sy_snum         │     0 │
└─────────────────┴───────┘
  12 rows       2 columns
```

## Explicación del query para quality_w03a

La tabla `quality_w03a` se crea utilizando `UNION ALL` de tres consultas `SELECT` separadas, cada una calculando una métrica de calidad específica:

1. **Nulos en pl_name**: `SELECT '{run_ts}' AS run_ts, 'nulls_pl_name' AS check_name, (COUNT(*) - COUNT(pl_name))::BIGINT AS metric_value FROM raw_ps`

2. **Nulos en hostname**: `SELECT '{run_ts}' AS run_ts, 'nulls_hostname' AS check_name, (COUNT(*) - COUNT(hostname))::BIGINT AS metric_value FROM raw_ps`

3. **Fuera de rango en disc_year**: `SELECT '{run_ts}' AS run_ts, 'disc_year_range' AS check_name, COUNT(*)::BIGINT AS metric_value FROM raw_ps WHERE disc_year IS NOT NULL AND (disc_year < 1980 OR disc_year > 2026)`

Cada consulta devuelve el timestamp de ejecución, el nombre del check y el valor de la métrica. El `UNION ALL` combina estos resultados en una sola tabla para un reporte consolidado de calidad.