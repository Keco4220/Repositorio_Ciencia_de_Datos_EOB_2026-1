# Decisions Log

## W03 - Validación de cardinalidad antes de JOINs

- **Fecha:** 2026-03-09
- **Decisión:** Implementar validación sistemática de cardinalidad antes de realizar JOINs para evitar duplicación accidental de filas.
- **Razón:** Los JOINs pueden multiplicar filas cuando las claves no son únicas, llevando a cálculos incorrectos. Es crucial verificar que las dimensiones tengan exactamente 1 fila por clave antes de unir tablas.
- **Método:** 
  - Contar filas antes y después del JOIN
  - Verificar cardinalidad con consultas como `COUNT(DISTINCT key) = COUNT(*)` en dimensiones
  - Detectar duplicados con `GROUP BY key HAVING COUNT(*) > 1`
- **Evidencia:** En el análisis de `dim_host_bad`, un JOIN malo duplicó filas de 6,107 a 10,779 (76% más filas). Después de deduplicar con CTE, el JOIN correcto mantuvo las 6,107 filas originales. Query de validación: `SELECT hostname, COUNT(*) FROM dim_host_bad GROUP BY hostname HAVING COUNT(*) > 1` reveló múltiples hosts duplicados.