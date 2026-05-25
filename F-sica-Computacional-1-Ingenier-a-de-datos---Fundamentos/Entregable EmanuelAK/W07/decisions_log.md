# Decisions Log

---

## W06B — Entrada: Definición de métrica y umbral de rendimiento

**Fecha:** 2026-05-19  
**Autor:** Alejandro  
**Contexto:** Ejecución del runner `w06b_runner.py` sobre el dataset NASA Exoplanet PSCompPars (6 087 registros).

### Decisión

Definir como métrica de aceptación de rendimiento la siguiente regla:

> **`dims < 0.1 s`** — La etapa `dims` (consultas de conteo sobre tablas Gold) debe completarse en menos de 100 ms.  
> **`gold < 0.5 s`** — La etapa `gold` (star schema + 4 escrituras a SQLite) debe completarse en menos de 500 ms.

### Justificación

- `dims` es una consulta de lectura pura (`SELECT COUNT(*)`); si tarda más de 100 ms sobre ~6 000 filas en SQLite local, indica un problema de índices o bloqueo de DB.
- `gold` involucra I/O real (DROP + CREATE + INSERT × 4 tablas); 500 ms es un umbral conservador que tolera variación del SO pero alerta si el pipeline escala mal.

### Evidencia — Corrida 1

| Etapa  | Tiempo (s) | ¿Pasa umbral? |
|--------|-----------|---------------|
| bronze | 0.0536    | ✅ (sin umbral definido) |
| silver | 0.0642    | ✅ |
| gold   | 0.1047    | ✅ < 0.5 s |
| dims   | 0.0020    | ✅ < 0.1 s |

### Evidencia — Corrida 2

| Etapa  | Tiempo (s) | ¿Pasa umbral? |
|--------|-----------|---------------|
| bronze | 0.0531    | ✅ |
| silver | 0.0954    | ✅ |
| gold   | 0.1108    | ✅ < 0.5 s |
| dims   | 0.0017    | ✅ < 0.1 s |

### Conclusión

Ambas corridas superan todos los umbrales definidos con amplio margen. El pipeline es apto para el volumen actual del dataset. Si el dataset creciera 10× (~60 000 filas), se recomienda revisar si `gold` supera el umbral de 0.5 s y evaluar el uso de índices en SQLite o migración a DuckDB.
