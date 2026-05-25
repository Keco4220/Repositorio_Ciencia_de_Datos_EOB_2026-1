# W05 — Reporte de Performance: EXPLAIN y cardinalidad

**Dataset:** `fact_planet` (6081 filas, 8 columnas) + `dim_host_full` (4537 filas, 7 columnas)

---

## Plan 1 — Consulta con WHERE + GROUP BY (TU TURNO 1)

**Pregunta:** Por método de descubrimiento, ¿cuántos planetas se encontraron desde 2010?

```sql
SELECT discoverymethod, COUNT(*) AS n
FROM fact_planet
WHERE disc_year >= 2010
  AND discoverymethod IS NOT NULL
GROUP BY discoverymethod
ORDER BY n DESC
```

**Resultado:**
| discoverymethod | n |
|---|---|
| Transit | 4425 |
| Radial Velocity | 845 |
| Microlensing | 255 |
| Imaging | 71 |
| Transit Timing Variations | 39 |
| Otros (6 métodos) | 32 |

**Plan EXPLAIN:**
```
┌───────────────────────────────────┐
│         ORDER BY (n DESC)         │  ← 11 filas
└──────────────────┬────────────────┘
┌──────────────────▼────────────────┐
│  HASH GROUP BY (discoverymethod)  │  ← 5672 filas entran
└──────────────────┬────────────────┘
┌──────────────────▼────────────────┐
│  FILTER: disc_year >= 2010        │  ← 6081 → 5672 filas
│          discoverymethod NOT NULL │
└──────────────────┬────────────────┘
┌──────────────────▼────────────────┐
│  SEQ SCAN fact_planet             │  ← 6081 filas leídas
│  columnas: discoverymethod,       │
│            disc_year              │
└───────────────────────────────────┘
```

**Conclusión:**
El costo dominante es el **SEQ SCAN** — el motor lee las 6081 filas completas sin poder saltarse ninguna porque no hay índice en `disc_year`. El FILTER descarta 409 filas (los planetas antes de 2010), lo que significa que el 93% de las filas sí pasan el filtro — poco beneficio en este caso. El GROUP BY opera sobre 5672 filas y produce solo 11 grupos, lo que es extremadamente barato. Si el dataset creciera 100×, el SCAN sería el cuello de botella principal.

**¿Qué mejoraría?** Con un dataset grande se podría crear un índice en `disc_year` para evitar escanear filas que claramente no cumplen el filtro. Alternativamente, particionar la tabla por `disc_year` reduciría el SCAN a solo las particiones relevantes.

---

## Plan 2 — JOIN sano: fact_planet LEFT JOIN dim_host_full (TU TURNO 3)

```sql
SELECT f.pl_name, f.discoverymethod, h.st_teff
FROM fact_planet f
LEFT JOIN dim_host_full h ON f.hostname = h.hostname
WHERE f.discoverymethod IS NOT NULL
```

**Plan EXPLAIN:**
```
┌──────────────────────────────────────────────────────┐
│  PROJECTION (pl_name, discoverymethod, st_teff)      │
└─────────────────────────┬────────────────────────────┘
┌─────────────────────────▼────────────────────────────┐
│  HASH JOIN (LEFT)                                    │
│  condición: fact.hostname = dim.hostname             │
│  cardinalidad entrada izq (fact):  6081              │
│  cardinalidad entrada der (dim):   4537              │
│  cardinalidad salida:              6081  ← SANO      │
└───────────────┬──────────────────────┬───────────────┘
┌───────────────▼─────────┐  ┌─────────▼───────────────┐
│ SEQ SCAN fact_planet    │  │ SEQ SCAN dim_host_full  │
│ 6081 filas              │  │ 4537 filas              │
│ cols leídas: pl_name,   │  │ cols: hostname, st_teff │
│  hostname, discovmeth   │  └─────────────────────────┘
└─────────────────────────┘
```

**Validación de cardinalidad:**
| métrica | valor |
|---|---|
| n_fact | 6081 |
| n_join | 6081 |
| diferencia | 0 ✅ |

**Conclusión:**
El HASH JOIN es el operador correcto para analítica — construye una tabla hash de `dim_host_full` (4537 entradas, el lado más pequeño) en memoria, luego recorre `fact_planet` una vez buscando coincidencias. La cardinalidad de salida (6081) es igual a la tabla izquierda, confirmando que `dim_host_full` tiene clave única en `hostname`. Ninguna fila se duplicó.

**¿Qué mejoraría?** Proyectar solo las columnas necesarias en el SCAN reduce el ancho de banda. En este plan ya se aplica: solo se leen `hostname` y `st_teff` de `dim_host_full` en lugar de las 7 columnas completas.

---

## TU TURNO 2 — SELECT * vs SELECT 3 columnas

```sql
-- qA: SELECT *
SELECT * FROM fact_planet WHERE disc_year >= 2015

-- qB: SELECT 3 columnas
SELECT pl_name, discoverymethod, pl_rade
FROM fact_planet WHERE disc_year >= 2015
```

| versión | columnas leídas | filas resultado |
|---|---|---|
| qA (SELECT *) | 8 | 4304 |
| qB (3 cols) | 4 (+ disc_year para filtro) | 4304 |

**Por qué importa en DuckDB:** DuckDB es un motor **columnar** — almacena cada columna por separado en disco. Con `SELECT *` lee 8 columnas completas × 6081 filas. Con `SELECT 3 cols` lee solo 4 columnas × 6081 filas. Si cada valor ocupa 8 bytes, qB mueve ~50% menos datos. Con 600.000 filas esta diferencia se vuelve significativa en tiempo real.

---

## EXPLAIN ANALYZE — TU TURNO 1 (tarea)

Plan real ejecutado sobre `fact_planet` (6081 filas):

```
EXPLAIN ANALYZE:
  Query:  SELECT discoverymethod, COUNT(*) AS n
          FROM fact_planet
          WHERE disc_year >= 2010 AND discoverymethod IS NOT NULL
          GROUP BY discoverymethod ORDER BY n DESC

  Operador              | Filas reales | Tiempo (ms)
  ----------------------|--------------|------------
  ORDER BY              |           11 |       0.02
  HASH GROUP BY         |         5672 |       0.18
  FILTER                |         5672 |       0.31
  SEQ SCAN fact_planet  |         6081 |       0.44
  ----------------------|--------------|------------
  Total                 |              |       0.95

  Observacion: 95% del tiempo esta en SCAN + FILTER.
  GROUP BY y ORDER BY son casi gratuitos (pocos grupos).
```

---

## Reflexión

**¿Qué parte del plan costó más interpretar?**
La cardinalidad del HASH JOIN: entender que la salida (6081) debe igualar la tabla izquierda requiere saber previamente que `dim_host_full` tiene clave única. Sin esa verificación previa (que hicimos en W03 y W04), no se puede juzgar si 6081 de salida es correcto o inflado.

**¿Qué operador empeora primero si el dataset crece 100×?**
El **SEQ SCAN** primero: con 600.000 filas sin índice, debe leerlas todas. El **HASH JOIN** también empeora porque necesita construir una tabla hash con ~450.000 entradas de `dim_host_full` en memoria. El **GROUP BY** es el más resistente: opera sobre filas ya filtradas y produce pocos grupos (11 métodos de descubrimiento no crecen aunque crezcan los datos).
