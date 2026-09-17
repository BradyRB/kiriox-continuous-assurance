# Kiriox Continuous Assurance — Local

Base local-first para adquisición, validación e ingesta auditable de datos. El MVP procesa archivos cerca de su origen y usa PostgreSQL local como almacenamiento de trabajo; no envía datasets a servicios externos.

## Arquitectura

```text
Next.js / TypeScript (127.0.0.1:3000)
              |
FastAPI / Python (127.0.0.1:8000)
              |
PostgreSQL local (127.0.0.1:5432)

Source Manager → FileReader/Connector → Change Detector → Validator → Loader
                                  ↘ Audit Logger / quarantine / load_runs
```

La separación lógica vive en los schemas `ingestion`, `raw`, `data` y `audit`. El runtime usa migraciones Alembic; no crea tablas silenciosamente.

## Inicio rápido

Requisitos: Python 3.11+, Node 20+, Docker Desktop.

```powershell
docker compose up -d postgres
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL = "postgresql+psycopg://kiriox:kiriox@127.0.0.1:5432/kiriox"
$env:KIRIOX_MASTER_KEY = "dev-only-change-me-32-bytes-minimum"
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

En otra terminal:

```powershell
cd frontend
npm install
npm run dev
```

Abrir http://127.0.0.1:3000 y la documentación de API en http://127.0.0.1:8000/docs.

## Estado de esta entrega

Implementado: foundation local, migración reproducible, fuentes, carga/preview de CSV, TXT delimitado, XLSX read-only, XML incremental, reglas REQUIRED/NUMERIC/INTEGER/DECIMAL/DATE/MAX_LENGTH/ALLOWED_VALUES/MIN/MAX/RANGE/REGEX/UNIQUE, SHA-256 de archivo, hash canónico por fila, FULL_REPLACE/APPEND/INCREMENTAL_UPSERT, cuarentena, locking por fuente, historial, detalle de ejecución, auditoría de configuración y UI operativa. Iteración 2 añade `PostgreSQLConnector` read-only real, conexión cifrada, explorer de schemas/tablas/columnas, extracción por cursor con watermark compuesto, schedules persistentes, retries clasificables y Design System con tokens/AppShell/componentes compartidos. Iteración 3 añade wizard funcional de 8 pasos con preview independiente, reglas y schedule opcional, control activar/pausar, detalle enriquecido de runs, E2E automatizado de frontend, benchmark de reader y adapters SQLAlchemy para SQL Server, MySQL, MariaDB, Oracle y Db2.

Pendiente para un sprint de plataforma: E2E automatizado contra motores distintos de PostgreSQL, instalar y probar drivers/servidores de cada motor, benchmark de throughput PostgreSQL y autenticación multiusuario/RBAC.

## Garantías

- Bind local por defecto: `127.0.0.1`; no se configura `0.0.0.0`.
- Secretos: la implementación de credenciales usa Fernet (AES-128-CBC + HMAC autenticado en la librería actual) con master key fuera de PostgreSQL; la UI nunca devuelve password.
- Todas las consultas del `PostgreSQLConnector` son de lectura; los demás motores aún no están habilitados en este vertical.
- UTC internamente; la UI presenta el timezone configurado.
- Sin telemetría externa ni datasets enviados fuera del equipo.

## Tests

```powershell
cd backend
pip install -r requirements-dev.txt
pytest -q
```

Los tests unitarios cubren los cuatro casos fundamentales del encargo y reglas críticas. Los tests de PostgreSQL se ejecutan cuando `TEST_DATABASE_URL` apunta a una instancia local aislada.

Para generar datasets grandes sin añadirlos a Git:

```powershell
python scripts/generate_dataset.py --rows 1000000 --output work/transactions.csv
```

## Documentación

- [Arquitectura](docs/architecture.md)
- [Módulo de ingesta](docs/ingestion-module.md)
- [Conectores](docs/connectors.md)
- [Seguridad](docs/security.md)
- [Testing](docs/testing.md)
- [Guía de entrega a GitHub](docs/github-delivery.md)
- [Reporte del sprint para management](outputs/SPRINT-REPORT-FOR-MANAGER.md)
- [ADR](docs/adr/0001-local-first.md)
