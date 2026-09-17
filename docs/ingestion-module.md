# Módulo de ingesta

La API actual expone:

- `POST /api/sources`: configura una fuente y dataset.
- `POST /api/sources/{id}/preview`: preview limitado e inferencia de tipos.
- `POST /api/sources/{id}/rules`: añade una regla declarativa.
- `POST /api/sources/{id}/runs`: ejecuta una carga de archivo.
- `GET /api/sources/{id}/runs`: historial.
- `GET /api/runs/{id}/exceptions`: cuarentena.

El MVP acepta `.csv`, `.txt`, `.xlsx` y `.xml`. XML exige `reader_options.record_tag` explícito para no adivinar nodos. La clave de negocio es obligatoria para `APPEND` e `INCREMENTAL_UPSERT`; `FULL_REPLACE` usa staging transaccional y evita exponer reemplazos parciales.

Los hashes son SHA-256. Las filas se canonicalizan como una lista ordenada de pares `(columna, valor)`, con null explícito, strings recortados y fechas/decimales normalizados.
