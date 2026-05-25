# W06A — Evidencia: modelo con llaves (dim_host_sk + fact_planet_sk)

---

## dim_host_sk — validacion de cardinalidad

```sql
SELECT COUNT(*) AS n_rows, COUNT(DISTINCT hostname) AS n_keys
FROM dim_host_sk
```

| n_rows | n_keys |
|---|---|
| 4537 | 4537 |

**n_rows == n_keys** — cardinalidad 1:1 verificada. Cada hostname tiene exactamente un `host_id`. La surrogate key es unica y la dimension es valida para JOINs.

Primeros 5 registros (orden alfabetico por hostname):

| host_id | hostname |
|---|---|
| 1 | 11 Com |
| 2 | 11 UMi |
| 3 | 14 And |
| 4 | 14 Her |
| 5 | 16 Cyg B |

---

## fact_planet_sk — conteo y verificacion de huerfanos

```sql
SELECT COUNT(*) AS n_fact_sk FROM fact_planet_sk
```

| n_fact_sk |
|---|
| 6081 |

```sql
SELECT COUNT(*) AS orphan_rows
FROM fact_planet_sk f
LEFT JOIN dim_host_sk d ON f.host_id = d.host_id
WHERE d.host_id IS NULL
```

| orphan_rows |
|---|
| 0 |

**orphan_rows = 0** — integridad referencial perfecta. Todos los `host_id` en `fact_planet_sk` existen en `dim_host_sk`. La FK `fact_planet_sk.host_id -> dim_host_sk.host_id` esta completamente satisfecha.

---

## Diferencia entre modelo anterior y modelo con llaves

| Aspecto | Antes (hostname natural) | Ahora (host_id surrogate) |
|---|---|---|
| JOIN key | VARCHAR (hostname) | INTEGER (host_id) |
| Tamano en memoria | ~15 bytes por join | 4 bytes por join |
| Unicidad garantizada | Solo por convencion | Por PRIMARY KEY constraint |
| Integridad referencial | Manual (anti-join) | Por FOREIGN KEY constraint |
| Estabilidad si hostname cambia | Rompe todos los joins | Solo actualizar dim_host_sk |
