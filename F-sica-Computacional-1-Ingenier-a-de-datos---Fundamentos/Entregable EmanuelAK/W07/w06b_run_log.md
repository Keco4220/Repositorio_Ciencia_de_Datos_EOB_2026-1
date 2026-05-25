# W06B — Run Log

## Comando ejecutado
```bash
python -m src.pipeline.w06b_runner
```
_(ejecutado desde la raíz del proyecto)_

---

## STDOUT — Corrida 1

```
============================================================
  W06B Runner  —  2026-05-19T17:33:18.401263+00:00
============================================================
  [bronze] {'mode': 'bronze', 'rows_in': 6087, 'rows_out': 6087, 'seconds': 0.0536}
  [silver] {'mode': 'silver', 'rows_in': 6087, 'rows_out': 6087, 'seconds': 0.0642}
  [gold]   {'mode': 'gold', 'rows_in': 6087, 'rows_out': 6087, 'n_stars': 4541, 'n_methods': 11, 'seconds': 0.1047}
  [dims]   {'mode': 'dims', 'counts': {...}, 'seconds': 0.002}

────────────────────────────────────────────────────────────
  RESUMEN DE TIEMPOS
────────────────────────────────────────────────────────────
  bronze     0.0536s  ███████████████
  silver     0.0642s  ██████████████████
  gold       0.1047s  ██████████████████████████████
  dims       0.0020s  
────────────────────────────────────────────────────────────
  TOTAL            0.2269s
  Etapa más lenta: GOLD
```

## STDOUT — Corrida 2

```
  bronze     0.0531s
  silver     0.0954s
  gold       0.1108s
  dims       0.0017s
  TOTAL      0.2633s
  Etapa más lenta: GOLD
```

---

## Interpretación

### ¿Qué etapa fue la más lenta?

**GOLD** fue consistentemente la etapa más lenta en ambas corridas (~0.10–0.11 s).

Esto es esperable porque la etapa Gold realiza múltiples operaciones de mayor complejidad que las capas anteriores:

1. **Tres `merge` / join** sobre el DataFrame (~6087 filas) para asignar claves sustitutas de estrellas, métodos y años.
2. **Cuatro escrituras a SQLite** (`gold_dim_stars`, `gold_dim_methods`, `gold_dim_years`, `gold_fact_planets`), cada una con `to_sql(if_exists="replace")` que implica DROP + CREATE + INSERT.
3. **Deduplicación por múltiples columnas** para construir las dimensiones.

En comparación, Bronze solo hace una lectura CSV + un `to_sql`, y Silver hace transformaciones vectorizadas simples (apply, dropna, drop_duplicates).

### ¿Por qué cambian los tiempos entre corridas?

Los tiempos varían porque dependen del estado del sistema operativo en el momento de la ejecución:

- **Cache del SO**: en la 2ª corrida el archivo CSV ya está en caché de disco (page cache de Linux), pero SQLite debe igualmente hacer I/O para DROP/CREATE/INSERT.
- **Contención de recursos**: otros procesos del sistema pueden competir por CPU o I/O entre corridas.
- **Warm-up de Python**: el intérprete y las librerías (pandas, sqlite3) ya están cargados en la 2ª corrida, reduciendo ligeramente el tiempo de bronze pero no tanto el de gold (dominado por I/O a DB).
- **Garbage collector**: pandas puede activar el GC en puntos distintos entre corridas.

La variación total (~0.23 s vs ~0.26 s, ≈14%) es normal y dentro del margen de ruido para pipelines de esta escala.
