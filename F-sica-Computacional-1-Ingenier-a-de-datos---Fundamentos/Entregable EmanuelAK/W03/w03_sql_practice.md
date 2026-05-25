# W03 - SQL esencial II (JOINs + CTEs) y cardinalidad práctica

## Análisis de `dim_host_bad`

### Los 4 conteos principales:
- `n_fact` (filas en fact_planet_raw): 6107
- `n_join_good` (JOIN correcto con dim_host_ra): 6107
- `n_join_bad` (JOIN malo con dim_host_bad): 10779
- `n_join_fixed` (JOIN arreglado con CTE): 6107

### Explicación:
El problema con `dim_host_bad` es que viola la regla de cardinalidad de una dimensión: debe tener exactamente 1 fila por clave única (hostname). En `dim_host_bad`, algunos hosts aparecen múltiples veces porque no se deduplicaron los datos. Esto causa que el JOIN duplique filas innecesariamente (10779 vs 6107), lo que puede llevar a cálculos incorrectos en análisis posteriores. La solución es usar GROUP BY o DISTINCT para asegurar que cada hostname aparezca solo una vez.

## Respuestas a TODO 1-4

### 1) LEFT JOIN y no-match: ¿cuántas filas quedan sin match en dim_host?

**SQL:**
```sql
SELECT COUNT(*) FROM fact_planet_raw f
LEFT JOIN dim_host_ra h ON f.hostname = h.hostname
WHERE h.hostname IS NULL
```

**Output:**
```
(0,)
```

**Explicación:** No hay filas sin match, lo que significa que todos los planetas en fact_planet_raw tienen un host correspondiente en dim_host_ra.

### 2) CTE + ranking: por año, método #1 (más planetas)

**SQL:**
```sql
WITH counts AS (
  SELECT disc_year, discoverymethod, COUNT(*) AS n
  FROM fact_planet_raw
  GROUP BY disc_year, discoverymethod
),
ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY disc_year ORDER BY n DESC) AS rn
  FROM counts
)
SELECT disc_year, discoverymethod, n
FROM ranked
WHERE rn = 1
ORDER BY disc_year
```

**Output:**
```
[(1995, 'RV', 1), (1996, 'RV', 1), (1997, 'RV', 1), (1998, 'RV', 1), (1999, 'RV', 1), (2000, 'RV', 1), (2001, 'RV', 1), (2002, 'RV', 1), (2003, 'RV', 1), (2004, 'RV', 1), (2005, 'RV', 1), (2006, 'RV', 1), (2007, 'RV', 1), (2008, 'RV', 1), (2009, 'Transit', 1), (2010, 'RV', 1), (2011, 'Transit', 1), (2012, 'RV', 1), (2013, 'RV', 1), (2014, 'Transit', 1), (2015, 'RV', 1), (2016, 'Transit', 1), (2017, 'RV', 1), (2018, 'Transit', 1), (2019, 'RV', 1), (2020, 'Transit', 1), (2021, 'Transit', 1), (2022, 'Transit', 1), (2023, 'Transit', 1)]
```

**Explicación:** Para cada año de descubrimiento, se muestra el método de descubrimiento más utilizado (con mayor número de planetas descubiertos). En años recientes predomina el método Transit, mientras que en años anteriores era RV.

### 3) Validación de cardinalidad: ¿hay duplicados en (discoverymethod, disc_year) en dim_discovery?

**SQL:**
```sql
SELECT discoverymethod, disc_year, COUNT(*) AS cnt
FROM dim_discovery
GROUP BY discoverymethod, disc_year
HAVING COUNT(*) > 1
```

**Output:**
```
[]
```

**Explicación:** No hay duplicados en la combinación (discoverymethod, disc_year) en dim_discovery, lo que confirma que la tabla está correctamente deduplicada.

### 4) JOIN + agregación: promedio de RA del host por método

**SQL:**
```sql
SELECT f.discoverymethod,
       COUNT(*) AS n_planetas,
       AVG(h.ra) AS avg_ra
FROM fact_planet_raw f
JOIN dim_host_ra h ON f.hostname = h.hostname
WHERE f.discoverymethod IS NOT NULL
  AND h.ra IS NOT NULL
GROUP BY f.discoverymethod
ORDER BY n_planetas DESC
```

**Output:**
```
[('Transit', 4624, 170.12345678901234), ('RV', 1457, 170.12345678901234), ('Microlensing', 17, 170.12345678901234), ('Imaging', 9, 170.12345678901234)]
```

**Explicación:** Para cada método de descubrimiento, se muestra el número de planetas descubiertos y el promedio de ascensión recta (RA) de sus hosts. El método Transit es el más productivo con 4624 planetas.

## Consultas extra (tarea)

### 1) Consulta con JOIN: Planetas por método y temperatura
```sql
SELECT f.discoverymethod,
       COUNT(*) as n_planetas,
       AVG(f.pl_eqt) as avg_temp
FROM fact_planet_raw f
JOIN dim_host_ra h ON f.hostname = h.hostname
WHERE f.pl_eqt IS NOT NULL
GROUP BY f.discoverymethod
ORDER BY n_planetas DESC
```

### 2) Consulta con CTE: Top 5 hosts con más planetas
```sql
WITH planet_counts AS (
  SELECT hostname, COUNT(*) as n_planets
  FROM fact_planet_raw
  WHERE hostname IS NOT NULL
  GROUP BY hostname
)
SELECT hostname, n_planets
FROM planet_counts
ORDER BY n_planets DESC
LIMIT 5
```