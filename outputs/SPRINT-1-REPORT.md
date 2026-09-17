# Kiriox Continuous Assurance — Sprint 1

## A. Sprint completado

Base funcional local-first del módulo de ingesta, con el vertical de archivos, validación, trazabilidad y UI inicial.

## B. Funcionalidades implementadas

- FastAPI + SQLAlchemy + PostgreSQL local con bind loopback.
- Schemas `ingestion`, `raw`, `data`, `audit` y migración Alembic reproducible.
- Fuentes y datasets configurables por API/UI.
- Lectores CSV, TXT delimitado, XLSX read-only y XML incremental.
- Preview limitado, estimación de filas e inferencia de tipos.
- Validation Engine declarativo: REQUIRED, NUMERIC, INTEGER, DECIMAL, DATE, MAX_LENGTH, ALLOWED_VALUES, MIN, MAX, RANGE, REGEX y UNIQUE.
- SHA-256 de archivo y detección `FILE_UNCHANGED`.
- Canonicalización y hash determinista por fila.
- `FULL_REPLACE`, `APPEND` e `INCREMENTAL_UPSERT`, cuarentena y métricas de ejecución.
- Locking advisory por fuente, auditoría de creación y snapshot de configuración.
- Contrato `BaseConnector` explícito para PostgreSQL, SQL Server, MySQL, MariaDB, Oracle y Db2; los adapters de DB aún fallan explícitamente hasta su sprint.
- UI empresarial local en español para crear fuentes, cargar archivos, hacer preview y ejecutar cargas.
- Generador de datasets sintéticos configurable.

## C. Archivos principales

- `backend/app/readers.py`, `validation.py`, `hashing.py`, `pipeline.py`, `connectors.py`
- `backend/app/models.py`, `main.py`, `security.py`
- `backend/migrations/versions/0001_initial.py`
- `frontend/app/page.tsx`, `frontend/app/styles.css`
- `scripts/generate_dataset.py`, `scripts/start-backend.ps1`, `scripts/start-frontend.ps1`

## D. Arquitectura

Source Manager → Reader/Connector → Change Detection → Validation → Loader → PostgreSQL, con raw, quarantine, audit y load runs como evidencia persistente.

## E. Migraciones

`alembic upgrade head` genera correctamente la migración inicial en modo SQL offline. No pudo ejecutarse contra una instancia viva porque Docker Desktop no estaba disponible en el host durante la verificación.

## F. Tests

- Unit: PASS — `5 passed in 0.39s`.
- Integration PostgreSQL: no ejecutados; Docker daemon no disponible.
- API: no ejecutados contra DB viva; endpoints compilan y la app importa correctamente.
- E2E: pendiente del sprint de robustez.
- Frontend build: PASS — Next.js 16.3.5, TypeScript y generación estática completados.
- Ruff: PASS — todos los checks configurados.
- `npm audit --omit=dev`: PASS — 0 vulnerabilidades después de actualizar Next.js.

## G. Performance

Readers iterativos; XLSX read-only; XML `iterparse`; CSV/TXT por streaming; preview acotado; hash de archivo por chunks; raw insertado por batches.

## H. Riesgos y limitaciones reales

Scheduler, conectores reales de DB, explorador de tablas, watermark conectado a extracción DB y E2E aún quedan pendientes. El stack requiere PostgreSQL disponible para ejecutar cargas end-to-end. El bloqueo de Docker es ambiental, no una simulación silenciosa.

## I. Siguiente sprint

Completar PostgreSQLConnector read-only, scheduler persistente con retries/timezone/locking, explorador de schemas/tablas y ampliar pruebas de integración.

## J. Comandos

```powershell
docker compose up -d postgres
.\scripts\start-backend.ps1
.\scripts\start-frontend.ps1
```

## K. URLs

- UI: http://127.0.0.1:3000
- API/docs: http://127.0.0.1:8000/docs

## L. Credenciales demo

PostgreSQL local: `kiriox` / `kiriox`, solo para desarrollo local. No existe autenticación de usuario en esta etapa.

## M. Confirmaciones

- Datos enviados a cloud: **NO**.
- Secrets committed: **NO**; solo existe `.env.example` sin secreto real.
- DB source writes: **NO**; conectores de DB todavía no habilitados y el contrato es read-only.
- Idempotency verified: **YES**, con test de upsert y hash de archivo.
- Fundamental tests: **PASS**, 4 casos obligatorios cubiertos; suite total 5/5.
