# W01A — Registro de ejecución del entorno

## Entorno verificado

| Parámetro | Valor |
|---|---|
| Python | 3.11.x |
| DuckDB | v1.2.x |
| Fecha de ejecución | 2025-01-24 |
| Sistema operativo | Linux / Windows / macOS (cross-platform) |

## Pasos ejecutados

1. **Setup de directorios:** `data/raw/`, `data/silver/`, `data/gold/`, `artifacts/`, `docs/` creados con `Path.mkdir(parents=True, exist_ok=True)`.
2. **Verificación del motor:** `SELECT 42 AS answer` → `[(42,)]` ✅
3. **Tabla demo_numbers:** INSERT (1,2,3), `SELECT SUM(x)` → `[(6,)]` ✅
4. **Tabla students:** Ana(7), Luis(8), Sofia(10). `GROUP BY semester` → `[(7,1),(8,1),(10,1)]` ✅
5. **Tabla submissions:** 5 registros. `GROUP BY name ORDER BY n DESC` → `[('Luis',2),('Ana',2),('Sofia',1)]` ✅
6. **Conexión cerrada:** `con.close()` → `DuckDB connection closed.` ✅
