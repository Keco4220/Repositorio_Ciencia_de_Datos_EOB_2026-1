# W03 - Caso real de JOIN malo: Duplicación en análisis de exoplanetas

## Caso: Análisis de planetas por método de descubrimiento con información de host

### Problema identificado
Al intentar analizar la distribución de planetas por método de descubrimiento incluyendo información del host (RA), se observó una duplicación significativa de filas que distorsionaba los resultados del análisis.

### Evidencia con conteos

#### Antes del JOIN (datos correctos)
```sql
SELECT COUNT(*) FROM fact_planet_raw;
```
**Resultado:** 6107 filas

#### JOIN "malo" con tabla sin deduplicar
```sql
-- dim_host_bad: tabla creada sin GROUP BY, permitiendo duplicados
CREATE TABLE dim_host_bad AS
SELECT hostname, ra FROM raw_ps WHERE hostname IS NOT NULL;

-- JOIN que duplica filas
SELECT COUNT(*)
FROM fact_planet_raw f
JOIN dim_host_bad h ON f.hostname = h.hostname;
```
**Resultado:** 10779 filas (duplicación del 76%)

#### Después del fix (JOIN correcto)
```sql
-- Solución con CTE para deduplicar
WITH dim_host_fixed AS (
  SELECT DISTINCT hostname, ra
  FROM dim_host_bad
)
SELECT COUNT(*)
FROM fact_planet_raw f
JOIN dim_host_fixed h ON f.hostname = h.hostname;
```
**Resultado:** 6107 filas (sin duplicación)

### Diagnóstico: ¿Qué clave falló?

La clave que falló fue `hostname` en la tabla `dim_host_bad`. Esta tabla se creó directamente desde `raw_ps` sin deduplicar, lo que significa que hosts con múltiples planetas aparecían múltiples veces. Por ejemplo:

```sql
-- Evidencia de duplicados en dim_host_bad
SELECT hostname, COUNT(*) as cnt
FROM dim_host_bad
GROUP BY hostname
HAVING COUNT(*) > 1
ORDER BY cnt DESC
LIMIT 5;
```

Esta consulta revela que algunos hosts aparecen hasta 8 veces en la tabla "dimensión", violando la regla fundamental de que una dimensión debe tener exactamente 1 fila por clave única.

### Solución aplicada

#### Fix simple con GROUP BY
```sql
-- Crear dimensión correcta con GROUP BY
CREATE TABLE dim_host_correct AS
SELECT hostname, MAX(ra) AS ra
FROM raw_ps
WHERE hostname IS NOT NULL
GROUP BY hostname;
```

#### Fix alternativo con DISTINCT
```sql
-- Crear dimensión correcta con DISTINCT
CREATE TABLE dim_host_correct AS
SELECT DISTINCT hostname, ra
FROM raw_ps
WHERE hostname IS NOT NULL;
```

### Impacto del problema

Este tipo de JOIN malo puede llevar a:
- **Cálculos incorrectos:** Conteos, promedios y sumas inflados
- **Análisis erróneos:** Distribución de métodos de descubrimiento distorsionada
- **Decisiones equivocadas:** Basadas en datos duplicados

### Lección aprendida

Siempre validar cardinalidad antes de JOINs:
1. Verificar que dimensiones tengan `COUNT(DISTINCT key) = COUNT(*)`  
2. Contar filas antes/después de cada JOIN
3. Usar GROUP BY o DISTINCT para asegurar unicidad en dimensiones