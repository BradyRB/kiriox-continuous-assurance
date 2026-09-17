# Kiriox Continuous Assurance — Iteración 2

## A. Estado general

PARCIALMENTE VALIDADO. El vertical se ejecutó contra PostgreSQL 16 real en Docker Desktop, con migración limpia, connector read-only, cargas DB/file, watermark compuesto, scheduler persistente y UI local. SQL Server, MySQL/MariaDB, Oracle y Db2 permanecen fuera de alcance.

## B. Validación del Sprint existente

PostgreSQL real: PASS

Alembic desde DB vacía: PASS

File E2E: PASS

Se verificaron los schemas `ingestion`, `raw`, `data` y `audit`; la base limpia quedó en revisión `0002_scheduler_and_quarantine`.

## C. PostgreSQL Connector

Funciona realmente:

- conexión con `psycopg` y prueba de versión/usuario/base;
- modo `default_transaction_read_only=on`;
- discovery de schemas, tablas y columnas;
- preview limitado a 1–100 filas;
- identifiers SQL validados y quoted con `psycopg.sql.Identifier`;
- extracción con cursor nombrado y `fetchmany`;
- cierre explícito de conexión;
- API FastAPI para conexión, discovery, preview y ejecución DB.

## D. Watermark

El estado confirmado vive en `ingestion.watermarks` y solo se actualiza dentro de la misma transacción local que escribe `raw`, `data`, cuarentena y auditoría.

Cuando se configuran columna temporal y clave primaria, la condición es:

```sql
(watermark_column > last_value)
OR (watermark_column = last_value AND primary_key > last_primary_key)
```

La consulta ordena por ambas columnas. El E2E real con empate temporal leyó y persistió el siguiente registro correctamente. Un fallo técnico inyectado después de leer una fila conservó el watermark anterior; el reintento leyó las dos filas pendientes y avanzó de `id=9` a `id=11`.

## E. Scheduler

- persistencia en `ingestion.schedules`;
- frecuencias manual, horaria, cada X horas, diaria, semanal, mensual y cron;
- timezone-aware con almacenamiento UTC;
- locking por fila con `FOR UPDATE SKIP LOCKED` y advisory lock por fuente;
- `last_run_at` y `next_run_at` persistidos;
- retry exponencial solo para errores técnicos clasificables;
- ejecución en background al iniciar FastAPI;
- UI para crear y visualizar schedules persistidos.

## F. Seguridad

Credential encryption: PASS

Secrets in logs: PASS

Source write permissions: PASS

La password se cifra con Fernet usando `KIRIOX_MASTER_KEY`, no se devuelve en `ConnectionOut` y no se acepta dentro de `source.config`. La cuenta de prueba `source_auditor` recibió `permission denied` al intentar insertar en la fuente externa.

## G. UI / Kiriox Design System

- Tokens consolidados en `frontend/styles/tokens.css`: bosque, verde Kiriox, mint, superficies, borde, estados semánticos, spacing, radios, sombra, tipografía y transición.
- Paleta: `forest #17312d`, `green #137d6c`, `teal #2b9a86`, fondos claros y estados success/warning/error/info.
- `AppShell` y `Sidebar` compartidos, con navegación responsive móvil.
- Componentes reutilizables: `Button`, `Card`, `StatusBadge`, `EmptyState`, `PageHeader`, `Stepper` y `MetricCard`.
- Pantallas: fuentes, wizard de archivo, validation builder, explorador PostgreSQL funcional, historial, excepciones, schedules y configuración.
- El explorador consume schemas, tablas, columnas y preview desde la API; permite crear una fuente PostgreSQL desde la tabla seleccionada.
- Estados visuales: empty, loading, error, status badges, tablas densas y toast de resultado.
- Accessibility: labels nativos, botones semánticos, navegación responsive y `role=status` para mensajes.

Se consolidaron tokens desde la UI actual de Kiriox; no se introdujo un tema SaaS de terceros. La vista responsive fue inspeccionada en el navegador local. La comparación instrumental específica a 1366px y 1440px+ queda pendiente.

## H. Tests

Unit: 11/11

Integration: 20/20 escenarios locales PostgreSQL

API: 10/10 verificaciones manuales FastAPI

Frontend: 2/2 (`npm run lint`, `npm run build`)

E2E: 15/15 escenarios reales/manuales

## I. Performance

No se ejecutó benchmark de volumen; no se inventan métricas de throughput o latencia. La implementación usa batch configurable de 5.000 por defecto, cursor servidor y `fetchmany`; los E2E funcionales usaron datasets pequeños.

## J. Limitaciones reales

- Los escenarios PostgreSQL son una matriz manual reproducible, no un fixture automatizado completo bajo `TEST_DATABASE_URL`.
- No se ejecutó E2E completo de navegador con Playwright ni comparación instrumental de 1366/1440px.
- El wizard visual aún es un flujo compacto de cuatro pasos; no hay persistencia de borrador paso a paso.
- El historial no tiene todavía una vista de detalle enriquecida con todo el snapshot y raw record.
- No hay autenticación multiusuario ni RBAC; es una aplicación local-first.
- No se habilitaron otros motores de base de datos.

## K. Comandos exactos

PostgreSQL:

```powershell
docker compose up -d postgres
docker compose ps
docker compose exec -T postgres pg_isready -U kiriox -d kiriox
```

Backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
$env:DATABASE_URL = "postgresql+psycopg://kiriox:kiriox@127.0.0.1:5432/kiriox"
$env:KIRIOX_MASTER_KEY = "dev-only-change-me-32-bytes-minimum"
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Tests:

```powershell
cd backend
pytest -q
cd ..
ruff check backend/app backend/tests scripts --output-format concise
cd frontend
npm run lint
npm run build
npm audit --audit-level=high
```

## L. URLs

UI: [http://127.0.0.1:3000](http://127.0.0.1:3000)

API: [http://127.0.0.1:8000](http://127.0.0.1:8000)

Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## M. Confirmaciones

Datos enviados a cloud: NO

Secrets committed: NO

DB source writes: NO

Idempotency: PASS

Watermark failure safety: PASS

Concurrent-run protection: PASS

File fundamental tests: PASS

PostgreSQL incremental test: PASS

Scheduler persistence: PASS

Kiriox Design System: PASS

Visual consistency: FAIL — la revisión a 1366px/1440px+ no fue instrumentada en esta iteración.
