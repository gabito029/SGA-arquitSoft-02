# Evidencias de los atributos de calidad — incremento 001

Resultados de los escenarios de calidad de
[docs/01-analisis-de-sistema/08-escenarios-atributos-calidad.md](../docs/01-analisis-de-sistema/08-escenarios-atributos-calidad.md)
(EQ-01 a EQ-09), medidos el 2026-11-24 en la rama `001-flujo-solicitud`. El entorno fue Docker
Compose en un solo equipo (Windows 11, 16 núcleos lógicos, 15,4 GB de RAM), con PostgreSQL 16, una
instancia de la API (un proceso uvicorn) y Nginx. k6 v2.4.0 corrió en el mismo equipo. Por
desviación aprobada en la constitución v1.2.0, las pruebas de carga usan **k6 en lugar de Locust**
y conservan el estímulo y las medidas de `docs/`.

## Resumen por escenario

| Escenario | Cómo se probó | Herramienta | Métrica objetivo | Resultado obtenido | ¿Cumple? | Evidencia |
|---|---|---|---|---|---|---|
| **EQ-01** Seguridad | Matriz de cada usuario (12, de la jurisdicción y de fuera de ella) × cada acción (enviar, firmar, rechazar, despachar, acta) × cada estado. También sin token, consultas ajenas, borradores y usuarios sin jurisdicción. Además, la colección de Postman | pytest + httpx; Newman | 100 % de los intentos no autorizados rechazados | 536 de 536 casos (100 %): 351 acciones denegadas (403/404/409), 9 permitidas, 108 consultas ajenas con 404, 9 sin token con 401. Newman: 67 de 67 aserciones | ✅ Sí | [resumen-eq01.json](EQ-01/resumen-eq01.json) · [newman-001.html](EQ-01/newman-001.html) |
| **EQ-02** Integridad | Con el disparador de inmutabilidad desactivado dentro de la prueba, se alteran 11 datos firmados (recibido, solicitado, despachado, observación, firmante, fecha, decisión, bytes de la firma, huella) y se llama a `/verificacion`. También se descartan falsos positivos después del despacho y del acta | pytest + cryptography (Ed25519) | 100 % de las alteraciones detectadas | 14 de 14 casos: 11 alteraciones dan ALTERADA en el nivel exacto y 3 etapas sin alteración dan INTEGRA. El PDF firmado se valida en 002 (DT-01) | ✅ Sí | [resumen-eq02.json](EQ-02/resumen-eq02.json) |
| **EQ-03** Consistencia del inventario | Dos hilos con conexiones propias despachan 7 + 7 de un ítem con stock 10, mientras se retiene el bloqueo para forzar el choque. Se repite 3 veces y una consulta SQL compara el stock con Σ movimientos | pytest + PostgreSQL | 0 diferencias entre stock y movimientos; stock nunca negativo | 3 de 3 corridas: un 201 y un 409 `STOCK_INSUFICIENTE`, stock final 3, 0 diferencias | ✅ Sí | [resumen-eq03.json](EQ-03/resumen-eq03.json) |
| **EQ-04** Rendimiento | 20 VU durante 5 min con 1 s de pausa: 60 % bandeja, 30 % detalle y 10 % registro. Una corrida con la caché del catálogo activa y otra con `CATALOGO_CACHE_ACTIVA=false` | k6 | p95 < 2 s con 20 usuarios; errores < 1 % | Con caché: p95 **40,8 ms**, 19,5 req/s, 0 % de errores. Sin caché: p95 **1 010 ms**, 14,8 req/s, 0 % de errores. La mezcla aún no incluye "firmar" (el estímulo de `docs/` sí): queda para la corrida formal de 002 | ✅ Sí (en ambas corridas) | [k6-resumen-001.json](EQ-04/k6-resumen-001.json) · [sin caché](EQ-04/k6-resumen-001-sin-cache.json) · [análisis](EQ-04/analisis-bd-cache-001.json) |
| **EQ-05** Usabilidad | Pruebas Jest del formulario (máximo 5 campos), etiquetas en todos los campos, foco visible, contraste calculado (texto ≥ 5,8:1; bordes de campo 4,8:1) y vista a 360 px | Jest; revisión manual | Máximo 5 campos; Lighthouse ≥ 80 en accesibilidad y buenas prácticas (modo celular) | Formulario con 5 campos o menos (Jest). **Lighthouse no se ejecutó**: la medición formal queda para 002 | ⏳ Parcial | [jest-cobertura-001.txt](EQ-07/jest-cobertura-001.txt) |
| **EQ-06** Disponibilidad | No se ejecutó en 001 (la API tiene `restart: always` y un healthcheck en Compose) | Uptime Kuma + `docker kill` (previsto) | Vuelve a responder en menos de 1 min | Pendiente para 002. Dato relacionado: tras la saturación de la prueba de estrés, `/health` respondió en cuanto se cortó la carga | ⏳ Pendiente | — |
| **EQ-07** Mantenibilidad | Cobertura de los módulos críticos y análisis estático. El umbral del COLOGE se lee de la configuración (`UMBRAL_MONTO_ALTO`) y una prueba lo cambia sin tocar el código. La prueba formal del cambio de regla es de 002 | pytest-cov, Jest, Ruff, ESLint | Cobertura ≥ 60 % en los módulos críticos; 0 errores de análisis | pytest 98,4 % (requests 99 %, rules 100 %, signing 97 %, inventory 99 %). Jest 100 % de líneas en `src/logica`, `src/auth` y `src/api`. Ruff y ESLint con 0 errores | ✅ Sí (cobertura y análisis) · ⏳ cambio de regla formal en 002 | [cobertura por módulo](EQ-07/cobertura-por-modulo-001.txt) · [HTML backend](EQ-07/backend-cobertura-html/index.html) · [HTML frontend](EQ-07/frontend-cobertura-html/index.html) · [ruff](EQ-07/ruff-001.txt) · [eslint](EQ-07/eslint-001.txt) |
| **EQ-08** Trazabilidad | Se recorre el flujo completo (envío, visto bueno, conformidad, aprobación, despacho, acta). `/historial` y una consulta SQL confirman usuario, rol, órgano y fecha. Se recalcula la cadena de auditoría y se comprueba que no hay endpoints de escritura sobre el historial. Adaptado a 001: sin el nivel del COLOGE | pytest + PostgreSQL; Newman | 100 % de las firmas y rechazos con usuario, órgano y fecha | 6 de 6 pasos (100 %), cadena de auditoría íntegra, 0 endpoints de escritura (DELETE/PUT/PATCH/POST responden 405) | ✅ Sí (adaptado a 001) | [resumen-eq08.json](EQ-08/resumen-eq08.json) · [newman-001.html](EQ-08/newman-001.html) |
| **EQ-09** Escalabilidad | 40 VU durante 5 min con la mezcla de EQ-04: primero con 1 instancia y luego con `docker compose up --scale api=2`, con Nginx repartiendo (5 882 / 5 743 peticiones por instancia) | k6 + Nginx | Con 2 instancias y 40 usuarios, p95 < 2 s | 1 instancia: p95 **58,8 ms**, 38,7 req/s. 2 instancias: p95 **48,2 ms**, 38,6 req/s, 0 % de errores (un máximo aislado de 7 s) | ✅ Sí | [1 instancia](EQ-09/k6-eq09-1-instancia.json) · [2 instancias](EQ-09/k6-eq09-2-instancias.json) |
| **Estrés** (constitución, principio VII) | Carga progresiva 50 → 200 → 500 → 1 000 → 2 000 VU (1 min de subida y 2 min de meseta por escalón) | k6 | Registrar p95, errores y punto de quiebre | Llegó a **2 000 VU** activos (848 de 960 s; 52 197 iteraciones). **Punto de quiebre: ~80–100 VU**, donde el throughput se estanca en ~70 req/s. Latencia media estimada: 0,03 s (50 VU), 1,8 s (200), 5,9 s (500), 13,9 s (1 000), 34 s (2 000). 0 errores registrados. Ver la nota abajo | ⚠️ Registrado (interrumpido al 88 %) | [análisis](ESTRES/estres-2000-analisis.json) · [progreso de k6](ESTRES/k6-estres-progreso.log) |

**Nota sobre la prueba de estrés.** A los 848 s, con los 2 000 VU activos, Claude Code detuvo la
corrida porque el equipo se quedó con poca memoria (k6 ocupaba ~770 MB junto a Docker). k6 se cerró
a la fuerza y no alcanzó a escribir su `--summary-export`. Por eso no hay p95 por escalón: el
throughput sale del registro de progreso de k6 (una línea por segundo) y la latencia media se
estima con la ley de Little (VU / throughput − 1 s de pausa). La degradación se debe a la CPU de la
API, no a la base de datos. Hay un solo proceso uvicorn, que se estabiliza en 125–150 % de CPU,
mientras PostgreSQL se mantiene entre 11 % y 37 %. Para la corrida formal de 002 conviene: correr
k6 en otra máquina, usar varios workers o instancias de la API y exportar un resumen por escalón.

## Análisis de la base de datos y de la caché

Fuentes: diferencias de `pg_stat_database` antes y después de cada corrida, `pg_stat_user_tables`
y `EXPLAIN (ANALYZE, BUFFERS)` de la bandeja. Están en
[analisis-bd-cache-001.json](EQ-04/analisis-bd-cache-001.json).

**Caché del catálogo (EQ-04, 20 VU).** La caché en memoria con un TTL de 300 s guarda los órganos,
los almacenes y los ítems activos. La bandeja y el detalle la consultan por cada solicitud que
muestran: unidad, Gran Unidad y almacén.

| Medida | Con caché | Sin caché | Efecto de la caché |
|---|---|---|---|
| p95 global | 40,8 ms | 1 010 ms | 25 veces menor |
| p95 bandeja (20 solicitudes por página) | 34,2 ms | 1 088,7 ms | 32 veces menor |
| p95 detalle | 28,0 ms | 172,4 ms | 6 veces menor |
| p95 registro | 61,2 ms | 363,3 ms | 6 veces menor |
| Throughput | 19,5 req/s | 14,8 req/s | +31 % |
| Filas obtenidas en PostgreSQL por petición | 8,6 | 158,4 | 18 veces menos |
| Bloques leídos (caché de PostgreSQL) por petición | 122 | 347 | 2,8 veces menos |
| Errores | 0 % | 0 % | — |

Con 20 VU y 1 s de pausa, el máximo teórico es ~20 req/s. Con caché el sistema queda en ese techo
(19,5); sin caché baja a 14,8 porque cada iteración dura más (p95 de 1 s). La caché es lo que
mantiene la bandeja muy por debajo de la meta de 2 s, y conviene conservarla en 002. Advertencia:
es por proceso, así que con `--scale api=2` cada instancia tiene la suya. Sirve porque el catálogo
es casi estático; si cambiara a menudo, habría que invalidarla o usar una caché compartida.

**PostgreSQL.**

- **Lecturas de disco: 0 a 5** en todas las corridas, con un acierto de caché de PostgreSQL del
  **99,99 %**: todo el trabajo se resuelve en memoria y la base no es el cuello de botella, ni
  siquiera con 2 000 VU (CPU de la base entre 11 % y 37 %).
- **~2 transacciones por petición** en todas las corridas: las Unidades de Trabajo no se fragmentan
  al aumentar la carga.
- **La bandeja hace Seq Scan.** Las pruebas de carga dejaron 9 469 solicitudes, todas de BIM-11. La
  consulta `WHERE unidad_id = … ORDER BY creado_en DESC, id LIMIT 20` recorre toda la tabla
  (230 bloques, 3,6 ms) porque el índice `(unidad_id, estado, creado_en DESC)` no sirve para ese
  orden cuando no se filtra por estado. El efecto ya se nota: las filas recorridas por petición
  pasaron de 1 644 (con 640 solicitudes) a 10 540 (con 8 319). Esa cifra crece de forma lineal con
  la tabla. Recomendación para 002: un índice `(unidad_id, creado_en DESC, id)` (y los
  equivalentes por `gran_unidad_id` y `almacen_id`), y medir de nuevo.
- `requerimiento` acumula 111 627 Seq Scans y `item_requerimiento` 19 691, frente a 95 812 y
  781 508 usos de índice. Los catálogos (`organo`, `almacen`, `item`) se leen casi siempre por
  índice, aunque con la caché activa esas lecturas bajan mucho.

**Observaciones.** Las corridas se hicieron sobre la base de datos de la demo. Por eso cada corrida
empezó con más solicitudes que la anterior (de 640 a 8 319). Eso favorece un poco a la corrida con
caché, que se hizo antes que la sin caché, pero no explica una diferencia de 25 veces. Las
solicitudes creadas por k6 quedan en esa base.

## Otras evidencias

- [SC-009](SC-009/LEEME.md): ensayo de los pasos 1 a 10 del quickstart por la API. Falta
  cronometrar el ensayo desde la web.
- Comandos para reproducir: `k6 run -e CONTRASENA=… --summary-export ../../evidencias/EQ-04/k6-resumen-001.json k6/eq04_rendimiento.js`
  desde `tecnologia/pruebas/` (para EQ-09 y el estrés, el mismo comando con `k6/eq09_escalabilidad.js`
  y `k6/estres_2000.js`). La caché se desactiva con `CATALOGO_CACHE_ACTIVA=false` en el entorno de la
  API, y la segunda instancia se levanta con `docker compose up -d --scale api=2 api`.
