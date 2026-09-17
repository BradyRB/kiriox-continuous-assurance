# Kiriox Continuous Assurance — Sprint Completion

## Estado

El MVP local-first queda funcionalmente cerrado para archivos y extracción SQL read-only. Se completaron los pendientes directamente accionables del sprint: wizard multipaso, preview independiente, detalle enriquecido de runs, activar/pausar schedules, E2E de navegador y benchmark reproducible. En esta validación se ejecutó además un flujo E2E real con PostgreSQL local.

## Entregado

- Wizard funcional de 8 etapas: fuente, origen, preview, esquema, estrategia, validación, schedule y revisión.
- Preview temporal independiente de una fuente persistida.
- Preview HTTP probado con opciones multipart para CSV/TXT/XLSX/XML.
- Creación de reglas desde el wizard.
- Creación opcional de schedule al crear una fuente.
- Los schedules de archivos reutilizan el último archivo cargado cuando no se configura una ruta explícita.
- Vista de detalle de ejecución con métricas, watermark, errores, cuarentena, raw record y configuration snapshot.
- Activar/pausar schedules desde la UI.
- Adapters SQLAlchemy para SQL Server, MySQL, MariaDB, Oracle y Db2, con drivers opcionales y fallos explícitos cuando el driver no está instalado.
- Pruebas de navegador con Playwright.
- Benchmark reproducible de lectura streaming.
- Flujo E2E de archivo: fuente creada desde la UI, regla NUMERIC aplicada, 3 filas leídas, 2 insertadas y 1 rechazada; la excepción y su raw record quedaron visibles en historial.
- Flujo E2E PostgreSQL: conexión verificada, schemas/tablas/columnas descubiertos, preview de tabla, fuente creada desde el explorador y extracción con watermark; la segunda extracción leyó 0 filas.
- Schedule CRON probado: ejecución automática `FILE_UNCHANGED`, pausa y activación verificadas desde la UI.

## Validación

- Backend: 15 passed.
- Ruff: PASS.
- Frontend TypeScript/lint: PASS.
- Frontend build: PASS.
- E2E navegador: 2 passed.
- npm audit: 0 vulnerabilidades.
- Benchmark: 100.000 filas leídas a 1.114.406 filas/segundo en esta máquina; no es un SLO de producción.
- Responsive: PASS en 1920×1080, 1440×900 y 1366×768.

## Límites que requieren otro sprint o infraestructura

- E2E contra motores distintos de PostgreSQL: no ejecutable en este host porque no hay servidores ni drivers instalados.
- Benchmark de throughput PostgreSQL: pendiente de medir con un dataset grande contra la instancia local.
- Autenticación multiusuario y RBAC: requiere definir proveedor de identidad, roles, sesión y política de acceso; el producto actual es local-first monousuario.
- `mypy --strict`: falla por deuda de tipado previa en lectores, modelos, pipeline y endpoints; pytest/Ruff siguen pasando.

## Rutas

- UI: `http://127.0.0.1:3000/`
- API: `http://127.0.0.1:8000/`
- Docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`
