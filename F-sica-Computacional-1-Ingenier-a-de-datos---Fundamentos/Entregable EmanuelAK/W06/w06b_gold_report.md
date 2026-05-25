# W06B — Reporte Gold: outputs finales

**Modelo base:** `fact_planet_sk` (6081 planetas) JOIN `dim_host_sk` (4537 estrellas)

---

## gold_by_discoverymethod

```sql
CREATE VIEW gold_by_discoverymethod AS
SELECT
  discoverymethod,
  COUNT(*)               AS n_planets,
  ROUND(AVG(pl_rade), 4) AS avg_pl_rade,
  ROUND(AVG(pl_bmasse),4) AS avg_pl_bmasse,
  MIN(disc_year)         AS min_disc_year,
  MAX(disc_year)         AS max_disc_year
FROM fact_planet_sk
WHERE discoverymethod IS NOT NULL
GROUP BY discoverymethod
ORDER BY n_planets DESC
```

**Resultado completo:**

| discoverymethod | n_planets | avg_rade (R🜨) | avg_bmasse (M🜨) | yr_min | yr_max |
|---|---|---|---|---|---|
| Transit | 4487 | 4.365 | 123.8 | 2002 | 2026 |
| Radial Velocity | 1161 | 9.792 | 1039.8 | 1995 | 2026 |
| Microlensing | 265 | 9.860 | 800.5 | 2004 | 2026 |
| Imaging | 86 | 13.446 | 4498.6 | 2004 | 2026 |
| Transit Timing Variations | 39 | 6.493 | 484.4 | 2011 | 2025 |
| Eclipse Timing Variations | 17 | 12.893 | 2102.7 | 2009 | 2023 |
| Orbital Brightness Modulation | 9 | 9.645 | 350.3 | 2011 | 2021 |
| Pulsar Timing | 8 | 5.411 | 278.2 | 1992 | 2024 |
| Astrometry | 6 | 12.450 | 4673.6 | 2013 | 2025 |
| Pulsation Timing Variations | 2 | 12.750 | 2383.7 | 2007 | 2016 |
| Disk Kinematics | 1 | 13.300 | 794.6 | 2019 | 2019 |

**Interpretacion cientifica:**

Transit detecta planetas pequenos (avg 4.4 R🜨, masa relativamente baja) porque es sensible a planetas que cruzan su estrella — preferentemente orbitas cercanas y planetas no demasiado grandes. Radial Velocity e Imaging detectan planetas mucho mas masivos (avg 1040 y 4499 M🜨 respectivamente) porque estas tecnicas son mas sensibles a objetos grandes. Imaging tiene el promedio de masa mas alto porque detecta gigantes gaseosos a grandes distancias de su estrella — justo los objetos que Transit no puede ver. Pulsar Timing es el metodo mas antiguo (1992) y detecta planetas de tamano intermedio alrededor de estrellas de neutrones.

---

## gold_by_host

```sql
CREATE VIEW gold_by_host AS
SELECT d.host_id, d.hostname,
       COUNT(*) AS n_planets,
       ROUND(AVG(f.pl_rade), 3)   AS avg_pl_rade,
       ROUND(AVG(f.pl_bmasse), 3) AS avg_pl_bmasse
FROM fact_planet_sk f
JOIN dim_host_sk d ON f.host_id = d.host_id
GROUP BY d.host_id, d.hostname
ORDER BY n_planets DESC
```

**Top 10 sistemas:**

| host_id | hostname | n_planets | avg_rade (R🜨) | avg_bmasse (M🜨) |
|---|---|---|---|---|
| 1555 | KOI-351 | 8 | 3.900 | 31.1 |
| 4279 | TRAPPIST-1 | 7 | 0.979 | 0.9 |
| 399 | HD 10180 | 6 | 6.677 | 1587.7 |
| 441 | HD 110067 | 6 | 2.431 | 6.3 |
| 646 | HD 191939 | 6 | 6.590 | 177.0 |
| 714 | HD 219134 | 6 | 3.669 | 25.2 |
| 798 | HD 34445 | 6 | 8.855 | 86.7 |
| 989 | HIP 41378 | 6 | 4.254 | 7.8 |
| 1077 | K2-138 | 6 | 2.584 | 6.0 |
| 1678 | Kepler-11 | 6 | 2.967 | 7.9 |

**Interpretacion cientifica:**

KOI-351 (host_id=1555) lidera con 8 planetas confirmados — el sistema mas poblado del catalogo. TRAPPIST-1 (host_id=4279) es el mas notable: 7 planetas con radio promedio 0.98 R🜨, todos de tamano terrestre, orbitando una enana roja. Es el unico sistema en el top 10 donde todos los planetas son comparables a la Tierra en tamano. HD 10180 tiene 6 planetas pero con masa promedio de 1587 M🜨 (gigantes gaseosos), contrastando fuertemente con HD 110067 que tiene 6 planetas con solo 6 M🜨 promedio (super-Tierras). El `host_id` como surrogate key permite que estas consultas corran con JOINs enteros en lugar de comparaciones de strings, lo que es mas eficiente a escala.

---

## Por que estas metricas en Gold

Se eligieron `avg_pl_rade`, `avg_pl_bmasse`, `min/max_disc_year` porque son las preguntas mas frecuentes en analisis de exoplanetas: que tan grandes son los planetas detectados por cada metodo, que tan masivos, y desde cuando se detectan. Estas metricas resumen en una sola fila por grupo lo que de otro modo requeriria explorar miles de filas individuales.
