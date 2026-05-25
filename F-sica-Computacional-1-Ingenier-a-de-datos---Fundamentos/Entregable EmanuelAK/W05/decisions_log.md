# Decisions Log — W01

## Decisión 1 — Trazabilidad del Raw

- **Fecha:** 2025-01-24
- **Decisión:** Guardar SHA-256 del CSV raw en `artifacts/` por cada ejecución.
- **Razón:** Detectar cambios invisibles en el dato de origen (DDIA Cap.1 — reliability/operability). El archivo NASA puede actualizarse con el mismo nombre.
- **Alternativas consideradas:**
  - Confiar en el nombre del archivo → rechazada (no detecta cambios de contenido).
  - Usar solo fecha de descarga → rechazada (no es determinista si la fuente cambia).
- **Evidencia:** `raw_sha256=d89390c3ccfcced5e13815e9b5025057774ac0c0b958e1cab434ca97252531b3`, `n_rows=6087`, `n_cols=16`, `size_bytes=930507`.

## Decisión 2 — No editar el Raw

- **Fecha:** 2025-01-24
- **Decisión:** El archivo `data/raw/pscomppars.csv` no se modifica bajo ninguna circunstancia. Toda transformación ocurre en Silver o Gold.
- **Razón:** Principio de inmutabilidad del Raw (Bronze layer). Garantiza reproducibilidad completa del pipeline desde el origen.
- **Alternativas consideradas:** Corregir errores de formato directamente en el CSV → rechazada.

## Decisión 3 — disc_year=2026 no es error

- **Fecha:** 2025-01-24
- **Decisión:** Los 8 planetas con `disc_year=2026` se conservan tal como están en el Raw. No se filtran en Bronze.
- **Razón:** El catálogo NASA PSCompPars incluye publicaciones adelantadas (papers aceptados antes de su fecha formal). Eliminarlos en Raw violaría el principio de inmutabilidad; el filtro debe aplicarse en Silver si el curso lo requiere.
- **Evidencia:** Planetas afectados: TOI-5422 b, KMT-2022-BLG-1818L b/c, TOI-5789 b/d/e, TOI-5349 b, HIP 54515 b.

## Decisión 4 — Validar cardinalidad antes de cada JOIN (W03)

- **Fecha:** 2025-01-24
- **Decisión:** Antes de todo JOIN verificar que `n_rows = COUNT(DISTINCT clave)` en la tabla dimensión.
- **Razón:** Un JOIN contra una dimensión con duplicados multiplica filas silenciosamente. No lanza error. El resultado parece correcto pero está inflado. (DDIA Cap.2 — reliability de las relaciones entre tablas).
- **Evidencia:** `dim_host_bad` tenía 6087 filas con hostname duplicado. JOIN con `fact_planet_raw` produjo 10.743 filas en lugar de 6.087 — un 76.5% de inflación.
- **Alternativas:** Confiar en que la tabla ya es una dimensión válida → rechazada. Verificar solo visualmente → rechazada.
- **Fix estándar:** `SELECT COUNT(*), COUNT(DISTINCT clave) FROM dim_tabla` antes del JOIN.

## Decision 5 — Columnas del reporte de calidad W04A (12 columnas)

- **Fecha:** 2025-01-24
- **Decision:** Incluir en el reporte de nulos las 4 columnas de identificacion (pl_name, hostname, discoverymethod, disc_year), las 3 metricas planetarias principales (pl_orbper, pl_rade, pl_bmasse) y 4 del sistema (sy_dist, ra, dec, sy_snum, sy_pnum).
- **Razon:** Las columnas de identificacion son criticas para JOINs (nulos rompen relaciones). Las metricas planetarias son las mas usadas en Gold. Las del sistema contextualizan cada deteccion.
- **Evidencia:** pl_orbper tiene 321 nulos (5.27%) — la columna con mayor ausencia en las 12 seleccionadas.

## Decision 6 — Eliminar pl_rade > 30 en Silver

- **Fecha:** 2025-01-24
- **Decision:** Eliminar de silver_planet los 6 registros con pl_rade > 30 R_Tierra.
- **Razon:** Estos objetos (V2376 Ori b: 87.2 R🜨, HD 100546 b: 77.3 R🜨, etc.) son companeros de masa sub-estelar detectados por Imaging directo, no planetas convencionales. Su inclusion distorsiona estadisticas de radio planetario.
- **Alternativas:** Conservarlos con flag 'subthermal' -> viable pero fuera del scope del curso actual.
- **Evidencia:** 6 filas eliminadas. silver_planet: 6081 filas (raw_ps: 6087).

## Decision 7 — Regla extra Silver: pl_orbper > 0

- **Fecha:** 2025-01-24
- **Decision:** Agregar la regla (pl_orbper IS NULL OR pl_orbper > 0) al filtro Silver.
- **Razon:** Un periodo orbital negativo o cero es fisicamente imposible. Esta regla evita que errores de entrada en el catalogo propaguen valores sin sentido a Gold.
- **Evidencia:** 0 filas eliminadas en este dataset — el check es preventivo para versiones futuras del catalogo.

## Decision 8 — Reescritura de consulta para reducir costo de SCAN (W05)

- **Fecha:** 2025-01-24
- **Decision:** Reemplazar SELECT * por SELECT de columnas especificas en todas las consultas analiticas sobre fact_planet y silver_planet.
- **Razon:** DuckDB es un motor columnar. Leer columnas innecesarias transfiere datos extra desde memoria sin beneficio. En el TU TURNO 1, SELECT * leia 8 columnas; la consulta reescrita lee solo 3 (discoverymethod, disc_year, pl_rade) — 62.5% menos I/O.
- **Evidencia (EXPLAIN):** Plan A (SELECT *): SEQ_SCAN con 8 columnas. Plan B (SELECT 3 cols): SEQ_SCAN con 3 columnas. Mismo resultado, menor costo de transferencia.
- **Alternativas:** Crear indice sobre disc_year para convertir SEQ_SCAN en INDEX_SCAN — viable pero no necesario con 6081 filas. A considerar si el dataset crece 100x.

## Decision 8 — Reescribir SELECT * a SELECT columnas especificas (W05)

- **Fecha:** 2025-01-24
- **Decision:** Reemplazar SELECT * por SELECT de columnas especificas en todas las consultas de produccion.
- **Razon:** DuckDB es un motor columnar. SELECT * lee todas las columnas del almacenamiento aunque el resultado solo use 3. Con datos grandes esto duplica o triplica el I/O innecesariamente.
- **Evidencia (plan antes/despues):**
  - qA (SELECT * — 8 cols): lee 8 columnas x 6081 filas = ~390KB de datos movidos
  - qB (SELECT 3 cols): lee 4 columnas x 6081 filas = ~195KB — 50% menos I/O
  - Mismo resultado, mismo numero de filas (4304).
- **Alternativas:** Mantener SELECT * para simplicidad en exploracion (aceptable en notebooks) pero nunca en vistas Gold ni en exports a artifacts.
