# W08 Report — SQL Limpieza + Many-to-Many

**Fecha:** 2026-05-19  
**Dataset:** `pscomppars.csv` (NASA Exoplanet Archive — Planetary Systems Composite Parameters)

---

## Parte A — Limpieza Raw → Silver v2

### A1 — `method_map`

Se identificaron **11 métodos únicos** en la columna `discoverymethod` del dataset raw. Se creó la tabla `method_map` con mapeo directo de cada valor raw a su forma canónica en `snake_case`:

| raw_method | canonical_method |
|---|---|
| Transit | transit |
| Radial Velocity | radial_velocity |
| Microlensing | microlensing |
| Imaging | imaging |
| Transit Timing Variations | transit_timing_variations |
| Eclipse Timing Variations | eclipse_timing_variations |
| Orbital Brightness Modulation | orbital_brightness_modulation |
| Pulsar Timing | pulsar_timing |
| Astrometry | astrometry |
| Pulsation Timing Variations | pulsation_timing_variations |
| Disk Kinematics | disk_kinematics |

**Decisión de diseño:** se usó `snake_case` en minúsculas como forma canónica para garantizar consistencia con convenciones SQL y evitar problemas de case-sensitivity en futuros joins.

---

### A2 — `silver_planet_v2`

La tabla silver se construyó con un `CREATE TABLE AS SELECT` desde `raw_ps` con `LEFT JOIN` a `method_map`.

**Transformaciones aplicadas:**

| Campo | Transformación |
|---|---|
| `hostname_clean` | `LOWER(TRIM(hostname))` |
| `discoverymethod_clean` | `COALESCE(mm.canonical_method, LOWER(TRIM(discoverymethod)))` |
| `disc_era` | `CASE` por rango de `disc_year` |

**Checks de calidad:**

| Métrica | Resultado |
|---|---|
| Filas raw | 6 087 |
| Filas silver | 6 087 |
| Pérdida de filas | 0 |
| `hostname_clean` nulos | 0 |
| Métodos sin mapeo (`COALESCE` fallback) | 0 |

**Distribución por `disc_era`:**

| disc_era | n planetas |
|---|---|
| pre-2000 | 30 |
| 2000s | 380 |
| 2010s | 3 683 |
| 2020s | 1 994 |

**Distribución de `discoverymethod_clean` (top 5):**

| método | n |
|---|---|
| transit | 4 488 |
| radial_velocity | 1 161 |
| microlensing | 265 |
| imaging | 91 |
| transit_timing_variations | 39 |

---

## Parte B — Many-to-Many (toy schema)

### Esquema DDL

Se crearon tres tablas con PK/FK explícitas:

```sql
CREATE TABLE planet_demo(
  planet_id INTEGER PRIMARY KEY,
  name      VARCHAR NOT NULL
);

CREATE TABLE method_demo(
  method_id   INTEGER PRIMARY KEY,
  method_name VARCHAR NOT NULL UNIQUE
);

CREATE TABLE planet_method_demo(
  planet_id INTEGER NOT NULL,
  method_id INTEGER NOT NULL,
  PRIMARY KEY (planet_id, method_id),
  FOREIGN KEY (planet_id) REFERENCES planet_demo(planet_id),
  FOREIGN KEY (method_id) REFERENCES method_demo(method_id)
);
```

### Datos de ejemplo

4 planetas, 3 métodos, relaciones M:N:

| planeta | método(s) |
|---|---|
| 51 Peg b | Radial Velocity |
| HD 209458 b | Transit + Radial Velocity ✦ |
| Kepler-22 b | Transit |
| GJ 1132 b | Transit + Imaging ✦ |

✦ Planetas con 2 métodos de detección (demuestran la cardinalidad M:N).

### Q1 — Planetas por método

```sql
SELECT md.method_name, COUNT(DISTINCT pmd.planet_id) AS n_planets
FROM method_demo md
JOIN planet_method_demo pmd ON md.method_id = pmd.method_id
GROUP BY md.method_name
ORDER BY n_planets DESC;
```

| method_name | n_planets |
|---|---|
| Transit | 3 |
| Radial Velocity | 2 |
| Imaging | 1 |

### Q2 — Métodos por planeta

```sql
SELECT pd.name AS planet_name, COUNT(DISTINCT pmd.method_id) AS n_methods
FROM planet_demo pd
JOIN planet_method_demo pmd ON pd.planet_id = pmd.planet_id
GROUP BY pd.name
ORDER BY n_methods DESC;
```

| planet_name | n_methods |
|---|---|
| HD 209458 b | 2 |
| GJ 1132 b | 2 |
| 51 Peg b | 1 |
| Kepler-22 b | 1 |

### B2 — Check de duplicados en la link table

```sql
SELECT planet_id, method_id, COUNT(*) AS c
FROM planet_method_demo
GROUP BY planet_id, method_id
HAVING COUNT(*) > 1;
-- Resultado: 0 filas ✓
```

**Verificación de PK compuesta:** al intentar insertar `(2, 10)` por segunda vez, DuckDB lanza:
```
Constraint Error: Duplicate key "planet_id: 2, method_id: 10" violates primary key constraint.
```

Esto confirma que la PK compuesta en `planet_method_demo` bloquea duplicados correctamente.

---

## Conclusiones

- El dataset tiene **0 registros perdidos** en el paso raw → silver.
- El `COALESCE` sobre el `LEFT JOIN` con `method_map` garantiza que incluso si se agregan métodos nuevos en futuras versiones del dataset, no se pierdan filas (caen al fallback `LOWER(TRIM(...))`).
- El esquema M:N con link table y PK compuesta es la forma correcta de modelar relaciones muchos-a-muchos en SQL relacional; evita duplicados por diseño sin necesidad de lógica adicional en la aplicación.
