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
