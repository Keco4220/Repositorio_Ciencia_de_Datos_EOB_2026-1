# Glosario — Proyecto Exoplanetas (NASA PSCompPars)

| Término | Definición |
|---|---|
| **Bronze / Raw** | Dato tal como llega de la fuente original. No se edita. Vive en `data/raw/`. |
| **Silver** | Dato limpio, tipado y con reglas de calidad. Vive en `data/silver/`. |
| **Gold** | Marts y métricas listos para consumo analítico. Vive en `data/gold/`. |
| **pl_name** | Nombre del exoplaneta (ej. "Kepler-442 b"). Identificador único. |
| **hostname** | Nombre de la estrella anfitriona. |
| **discoverymethod** | Método de detección: Transit, Radial Velocity, Microlensing, Imaging, etc. |
| **disc_year** | Año de descubrimiento publicado. Puede incluir años futuros (papers adelantados). |
| **sy_snum** | Número de estrellas en el sistema. |
| **sy_pnum** | Número de planetas en el sistema. |
| **sy_dist** | Distancia al sistema estelar en parsecs. |
| **ra / dec** | Ascensión recta / Declinación (coordenadas celestes en grados). |
| **pl_orbper** | Período orbital en días. 321 valores nulos en el dataset. |
| **pl_rade** | Radio planetario en radios terrestres. |
| **pl_bmasse** | Masa planetaria (mejor estimación) en masas terrestres. |
| **pl_eqt** | Temperatura de equilibrio del planeta en Kelvin. Alta tasa de nulos (1539). |
| **st_teff** | Temperatura efectiva de la estrella en Kelvin. |
| **st_rad** | Radio estelar en radios solares. |
| **st_mass** | Masa estelar en masas solares. |
| **SHA-256** | Hash criptográfico que identifica de forma única el contenido de un archivo. |
| **Artifact** | Archivo de evidencia generado por el pipeline (JSON). Vive en `artifacts/`. |
| **DuckDB** | Motor SQL embebido columnar usado como warehouse local. |
| **Reliability** | (DDIA Cap.1) El sistema funciona correctamente incluso ante fallos inesperados. |
| **Scalability** | (DDIA Cap.1) Capacidad de manejar crecimiento de datos/carga. |
| **Maintainability** | (DDIA Cap.1) Facilidad de operar, entender y modificar el sistema. |
