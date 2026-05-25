# W02A — SQL esencial (práctica)

> Entrega: pega SQL + resultado (outputs) para Q1–Q10.

## Q1 - ¿Cuántos planetas hay por año? (top 15 años con más planetas)
SQL:
```sql
SELECT disc_year, COUNT(*) as n_planets
FROM raw_ps
WHERE disc_year IS NOT NULL
GROUP BY disc_year
ORDER BY n_planets DESC
LIMIT 15
```
Resultado:
- (2016.0, 1496)
- (2014.0, 869)
- (2021.0, 564)
- (2022.0, 369)
- (2023.0, 324)
- (2018.0, 315)
- (2024.0, 259)
- (2025.0, 240)
- (2020.0, 234)
- (2019.0, 196)
- (2015.0, 155)
- (2017.0, 152)
- (2012.0, 139)
- (2011.0, 135)
- (2013.0, 128)

## Q2 - Top 10 sistemas (hostname) con más planetas
SQL:
```sql
SELECT hostname, COUNT(*) as n_planets
FROM raw_ps
GROUP BY hostname
ORDER BY n_planets DESC
LIMIT 10
```
Resultado:
- ('KOI-351', 8)
- ('TRAPPIST-1', 7)
- ('TOI-178', 6)
- ('TOI-1136', 6)
- ('Kepler-80', 6)
- ('Kepler-20', 6)
- ('Kepler-11', 6)
- ('K2-138', 6)
- ('HIP 41378', 6)
- ('HD 34445', 6)

## Q3 - ¿Qué fracción de filas tiene pl_bmasse nulo?
SQL:
```sql
SELECT
  COUNT(*) as total_rows,
  COUNT(pl_bmasse) as non_null_mass,
  (COUNT(*) - COUNT(pl_bmasse)) as null_mass,
  ROUND((COUNT(*) - COUNT(pl_bmasse)) * 1.0 / COUNT(*), 4) as fraction_null
FROM raw_ps
```
Resultado:
- (6107, 6076, 31, 0.0051)

## Q4 - 10 planetas con mayor radio (pl_rade) (evita NULL)
SQL:
```sql
SELECT pl_name, pl_rade
FROM raw_ps
WHERE pl_rade IS NOT NULL
ORDER BY pl_rade DESC
LIMIT 10
```
Resultado:
- ('V2376 Ori b', 87.20586985)
- ('HD 100546 b', 77.3421)
- ('GQ Lup b', 33.6)
- ('Kepler-297 d', 32.6)
- ('PDS 70 b', 30.48848)
- ('DH Tau b', 30.2643)
- ('Kepler-1979 b', 29.33)
- ('TOI-1408 b', 25.0)
- ('CT Cha b', 24.66)
- ('HAT-P-67 b', 23.9872187)

## Q5 - Compara COUNT(*) vs COUNT(disc_year) por método
SQL:
```sql
SELECT
  discoverymethod,
  COUNT(*) as total_planets,
  COUNT(disc_year) as planets_with_year
FROM raw_ps
GROUP BY discoverymethod
ORDER BY total_planets DESC
```
Resultado:
- ('Transit', 4501, 4500)
- ('Radial Velocity', 1166, 1166)
- ('Microlensing', 266, 266)
- ('Imaging', 92, 92)
- ('Transit Timing Variations', 39, 39)
- ('Eclipse Timing Variations', 17, 17)
- ('Orbital Brightness Modulation', 9, 9)
- ('Pulsar Timing', 8, 8)
- ('Astrometry', 6, 6)
- ('Pulsation Timing Variations', 2, 2)
- ('Disk Kinematics', 1, 1)

## Q6 - Resumen por método: n_planets y promedio del periodo orbital
SQL:
```sql
SELECT
  discoverymethod,
  COUNT(*) as n_planets,
  AVG(pl_orbper) as avg_orbital_period
FROM raw_ps
WHERE pl_orbper IS NOT NULL
GROUP BY discoverymethod
ORDER BY n_planets DESC
```
Resultado:
- ('Transit', 4501, 23.972645441747453)
- ('Radial Velocity', 1166, 1754.316857572084)
- ('Transit Timing Variations', 39, 347.88883905753846)
- ('Imaging', 25, 17028014.904380802)
- ('Eclipse Timing Variations', 17, 3596.197317647059)
- ('Microlensing', 12, 4175.5575)
- ('Orbital Brightness Modulation', 9, 1.1726879777777777)
- ('Pulsar Timing', 7, 1475.7945579025713)
- ('Astrometry', 6, 865.2616666666667)
- ('Pulsation Timing Variations', 2, 1005.0)

## Q7 - Calidad de datos: Planetas con valores extremos de radio (> 50 radios terrestres)
**Pregunta:** ¿Qué planetas tienen radios extremadamente grandes que podrían indicar errores de medición o casos especiales?

SQL:
```sql
SELECT pl_name, pl_rade, hostname
FROM raw_ps
WHERE pl_rade > 50
ORDER BY pl_rade DESC
```
Resultado:
- ('V2376 Ori b', 87.20586985, 'V2376 Ori')
- ('HD 100546 b', 77.3421, 'HD 100546')

**Interpretación:** Solo 2 planetas tienen radios > 50 R⊕, lo que indica buena calidad general de los datos. Estos casos extremos merecen verificación adicional.

## Q8 - Calidad de datos: Duplicados por nombre de planeta
**Pregunta:** ¿Existen planetas con nombres duplicados que podrían indicar problemas de calidad de datos?

SQL:
```sql
SELECT pl_name, COUNT(*) as count
FROM raw_ps
GROUP BY pl_name
HAVING COUNT(*) > 1
ORDER BY count DESC
LIMIT 10
```
Resultado:
- (No hay duplicados)

**Interpretación:** No existen nombres de planetas duplicados, lo que indica buena integridad de los identificadores únicos.

## Q9 - Científica: Distribución de temperaturas de equilibrio por método de descubrimiento
**Pregunta:** ¿Cómo varían las temperaturas de equilibrio de los planetas según el método de descubrimiento?

SQL:
```sql
SELECT discoverymethod, COUNT(*) as n_planets, AVG(pl_eqt) as avg_temp_kelvin
FROM raw_ps
WHERE pl_eqt IS NOT NULL
GROUP BY discoverymethod
ORDER BY n_planets DESC
```
Resultado:
- ('Transit', 4283, 922.8979570394583)
- ('Radial Velocity', 196, 558.4645918367347)
- ('Imaging', 60, 1577.2683333333334)
- ('Transit Timing Variations', 21, 684.4285714285714)
- ('Microlensing', 5, 56.0)
- ('Orbital Brightness Modulation', 1, 2140.0)

**Interpretación:** Los planetas descubiertos por tránsito tienen temperaturas promedio de ~923K, mientras que los de imagen directa son mucho más calientes (~1577K), probablemente porque estos últimos orbitan más cerca de estrellas jóvenes masivas.

## Q10 - Científica: Relación masa-radio (densidad aproximada)
**Pregunta:** ¿Cuáles son los planetas más densos del dataset, calculando una aproximación de densidad como masa/radio³?

SQL:
```sql
SELECT pl_name, pl_bmasse, pl_rade,
       CASE
         WHEN pl_bmasse IS NOT NULL AND pl_rade IS NOT NULL
         THEN ROUND(pl_bmasse / (pl_rade * pl_rade * pl_rade), 4)
         ELSE NULL
       END as density_approx
FROM raw_ps
WHERE pl_bmasse IS NOT NULL AND pl_rade IS NOT NULL
ORDER BY density_approx DESC
LIMIT 10
```
Resultado:
- ('Kepler-80 f', 4459.73, 1.21, 2517.4013)
- ('Kepler-32 f', 969.228, 0.82, 1757.8604)
- ('Kepler-324 b', 2414.4, 1.14, 1629.6512)
- ('KOI-4777.01', 99.2, 0.51, 747.827)
- ('Kepler-238 b', 3305.02, 1.73, 638.3161)
- ('K2-137 b', 158.915, 0.64, 606.2126)
- ('Kepler-245 e', 1806.36, 1.75, 337.0468)
- ('KOI-2513.01', 7310.053361, 2.80224517, 332.2019)
- ('Kepler-37 e', 8.1, 0.37, 159.9116)
- ('Kepler-82 d', 885.098, 1.77, 159.6142)

**Interpretación:** Los planetas más densos son rocosos/terrosos con radios pequeños pero masas relativamente altas. Los valores extremos (>1000) sugieren planetas con composición rocosa densa o posibles errores de medición.

## Reflexión
- **¿Qué consulta te pareció más difícil y por qué?** La consulta Q10 (densidad aproximada) fue la más desafiante porque requería lógica condicional (CASE WHEN) y cálculo matemático (masa/radio³), además de manejar valores NULL correctamente.

- **Si el dataset creciera 100×, ¿qué consultas empeoran más y por qué?** Las consultas con ORDER BY sin LIMIT (como Q5 y Q9) empeorarían significativamente porque requieren ordenar tablas completas. Las consultas con GROUP BY también se volverían más costosas con más grupos. Las consultas con LIMIT (Q1, Q2, Q4) se mantendrían eficientes.