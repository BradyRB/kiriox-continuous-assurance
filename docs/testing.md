# Testing

`pytest -q` ejecuta 15 pruebas deterministas del detector de cambios, SHA-256, validación, preview acotado, watermark compuesto, cifrado de credenciales, retry classification, seguridad de identifiers, calendario timezone-aware, preview multipart y serialización segura de UUID. La verificación real de esta iteración ejecutó contra PostgreSQL local: migración desde `kiriox_test` vacía, conexión read-only, discovery, preview, streaming, carga inicial, delta con empate de timestamp, validación/cuarentena, FILE_UNCHANGED, rollback de FULL_REPLACE, locking, persistencia del scheduler, reintentos y seguridad del watermark ante fallo técnico.

Los escenarios PostgreSQL se ejecutan como una matriz E2E/manual contra los contenedores `kiriox`, `kiriox_test` y `external_source_test`; `TEST_DATABASE_URL` queda disponible para convertirlos en fixtures automatizados aislados. Frontend usa `npm run lint`, `npm run build` y `npm run test:e2e`, que cubre la navegación operativa y las ocho etapas del wizard.

Para una medición reproducible del reader por streaming:

```powershell
$env:PYTHONPATH = "backend"
python scripts/benchmark_reader.py --rows 100000
```

El benchmark reporta filas procesadas, segundos y filas por segundo; no representa todavía throughput de PostgreSQL ni debe interpretarse como SLO de producción.
