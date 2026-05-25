# Decisions Log

## W02 - Uso de SQLite en lugar de DuckDB

- **Fecha:** 2026-02-24
- **Decisión:** Usar SQLite como motor de base de datos principal en lugar de DuckDB para el curso de ciencia de datos.
- **Razón:** DuckDB presenta problemas de compatibilidad en Windows (errores de DLL) que impiden la ejecución en algunos entornos. SQLite está integrado en Python y no requiere dependencias externas, garantizando reproducibilidad.
- **Alternativas:**
  - Mantener DuckDB y requerir instalación manual de dependencias del sistema (rechazada por complejidad)
  - Usar pandas únicamente sin base de datos (rechazada por perder capacidades SQL)
  - Usar PostgreSQL/MySQL (rechazada por requerir servidor externo)
## W03A - Selección de 12 columnas para checks de calidad

- **Fecha:** 2026-03-09
- **Decisión:** Seleccionar 12 columnas clave para análisis de nulos: pl_name, hostname, disc_year, discoverymethod, pl_orbper, pl_rade, pl_bmasse, sy_dist, ra, dec, sy_snum, sy_pnum
- **Razón:** Estas columnas incluyen identificadores únicos, información de descubrimiento, propiedades físicas de planetas y sistemas estelares, que son críticas para análisis downstream y JOINs.
- **Evidencia:** La tabla de nulos muestra que pl_name, hostname y otras columnas clave tienen 0 nulos, mientras que propiedades opcionales como pl_orbper tienen 323 nulos, lo cual es aceptable.

## W03B - Reglas Silver aplicadas

- **Fecha:** 2026-03-09
- **Decisión:** Aplicar reglas de calidad para Silver: pl_name y hostname no nulos, disc_year en [1980,2026] si no nulo, pl_rade >0 y <=30 si no nulo, pl_bmasse >0 si no nulo, pl_orbper >0 si no nulo.
- **Razón:** Filtrar datos inválidos para asegurar integridad en análisis posteriores, evitando errores en cálculos y JOINs.
- **Evidencia:** Después de aplicar reglas, silver_planet tiene 6101 filas sin duplicados en pl_name, dim_host_full tiene 4554 filas únicas por hostname, y el JOIN fact-dim mantiene 6101 filas sin inflar.