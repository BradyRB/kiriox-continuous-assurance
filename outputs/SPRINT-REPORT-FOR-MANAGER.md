# Kiriox Continuous Assurance — Reporte de Sprint

**Fecha:** 17 de septiembre de 2026  
**Entrega:** MVP local-first de adquisición, validación e ingesta auditable  
**Estado:** Listo para revisión funcional y entrega del repositorio

## 1. Resumen ejecutivo

Durante este sprint se completó un módulo operativo para registrar fuentes de datos, inspeccionar archivos o tablas, validar registros, cargar cambios de forma controlada y conservar evidencia auditable de cada ejecución.

La entrega funciona localmente con una interfaz web, una API FastAPI y PostgreSQL. El flujo principal de archivos y el flujo real contra PostgreSQL fueron ejecutados y validados de extremo a extremo. El producto queda listo para revisión del negocio y demostración; autenticación multiusuario, servidores de otros motores y pruebas de rendimiento de PostgreSQL a gran escala quedan fuera del alcance de este MVP.

## 2. Qué puede hacer el módulo

### Configuración de fuentes

- Crear una fuente con nombre, descripción, tipo, dataset y clave de negocio.
- Definir origen FILE o conexión SQL de solo lectura.
- Seleccionar la estrategia FULL_REPLACE, APPEND o INCREMENTAL_UPSERT.
- Configurar comportamiento ante valores faltantes, tamaño de lote y columnas de watermark.
- Revisar y confirmar toda la configuración en un wizard de ocho pasos antes de guardar.

### Archivos y preview

- Procesar CSV, TXT delimitado, XLSX y XML.
- Mostrar un preview limitado antes de ejecutar.
- Inferir tipos como INTEGER, DECIMAL, DATE y TEXT.
- Exigir record_tag explícito para XML, evitando adivinar nodos incorrectos.
- Calcular SHA-256 del archivo y hash canónico por fila.

### Validación y cuarentena

- Crear reglas REQUIRED, NUMERIC, INTEGER, DECIMAL, DATE, MAX_LENGTH, ALLOWED_VALUES, MIN, MAX, RANGE, REGEX y UNIQUE.
- Clasificar errores como corregibles, rechazables o técnicos.
- Enviar registros inválidos a cuarentena sin perder el contenido original.
- Mostrar campo, valor recibido, regla, código de error y raw record.

### Carga segura

- Detectar archivos sin cambios y devolver FILE_UNCHANGED sin duplicar datos.
- Insertar nuevos registros y actualizar registros existentes según la estrategia elegida.
- Ejecutar FULL_REPLACE mediante staging transaccional para evitar reemplazos parciales.
- Usar locking por fuente para evitar ejecuciones simultáneas incompatibles.
- Confirmar el watermark únicamente después de una carga local exitosa.
- Hacer rollback ante fallos técnicos.

### Conectores SQL

- Conexión real read-only a PostgreSQL.
- Descubrimiento de schemas, tablas y columnas.
- Preview de tablas con límite controlado.
- Extracción streaming con cursor y watermark compuesto (columna, clave primaria).
- Adapters preparados para SQL Server, MySQL, MariaDB, Oracle y Db2 mediante drivers opcionales.
- Rechazo explícito cuando falta un driver o no existe la instancia; no se simulan resultados.

### Schedules y operación

- Crear schedules CRON o INTERVAL.
- Ejecutar cargas automáticas.
- Pausar y activar schedules desde la interfaz.
- Registrar estado, próxima ejecución, intentos y clasificación de reintentos.
- Usar el timezone configurado (America/Santo_Domingo en el entorno validado).

### Historial, evidencia y seguridad

- Consultar historial de ejecuciones por fuente.
- Ver métricas: recibidos, nuevos, actualizados, rechazados y duración.
- Ver watermark anterior y posterior.
- Consultar excepciones y detalle del raw record.
- Conservar snapshot de configuración de cada ejecución.
- Cifrar credenciales con Fernet y mantener la master key fuera de PostgreSQL.
- No devolver contraseñas a la UI.
- Trabajar por defecto en 127.0.0.1 y sin telemetría externa.

## 3. Flujo funcional completo para probarlo

### Paso 0 — Arranque

Desde la raíz del repositorio, en PowerShell:

```powershell
docker compose up -d postgres
.\\scripts\\start-backend.ps1
```

El backend debe quedar abierto en esa terminal. En una segunda terminal:

```powershell
.\\scripts\\start-frontend.ps1
```

Abrir http://127.0.0.1:3000/. Para comprobar la API, abrir http://127.0.0.1:8000/health; debe responder con estado saludable.

### Paso 1 — Crear una fuente de archivo

En Fuentes de datos, pulsar + Nueva fuente y completar el wizard:

1. **Fuente:** nombre Demo transacciones, una descripción y tipo FILE.
2. **Origen:** seleccionar archivo outputs/transacciones-invalidas.csv.
3. **Preview:** comprobar las columnas ID, Amount, TransactionDate, CustomerID y BranchID.
4. **Esquema:** confirmar tipos detectados; usar dataset transactions_demo y clave ID.
5. **Estrategia:** elegir INCREMENTAL_UPSERT.
6. **Validación:** crear regla para Amount, tipo NUMERIC, severidad ERROR.
7. **Schedule:** dejarlo vacío para una prueba manual o crear CRON */1 * * * * para probar automatización.
8. **Revisión:** verificar el resumen y pulsar Crear fuente y continuar.

La aplicación debe confirmar que la fuente fue creada, junto con su regla y schedule si se configuró.

### Paso 2 — Preview y ejecución

En la fuente recién creada:

1. Ejecutar Preview y verificar que el registro con Amount=ABC aparece como dato que incumple la regla.
2. Pulsar Ejecutar carga.
3. Esperar el resultado COMPLETED_WITH_ERRORS.

Con el archivo de ejemplo, el resultado esperado es:

| Métrica | Resultado |
|---|---:|
| Registros recibidos | 3 |
| Registros nuevos | 2 |
| Registros actualizados | 0 |
| Registros rechazados | 1 |
| Error | INVALID_NUMBER en Amount |

### Paso 3 — Historial y evidencia

Entrar en Historial de ejecuciones, seleccionar la fuente y abrir la ejecución recién creada. Validar:

- estado COMPLETED_WITH_ERRORS;
- las cuatro métricas de carga;
- la excepción de la fila con ID=2;
- valor recibido ABC;
- regla NUMERIC;
- código INVALID_NUMBER;
- raw record completo;
- snapshot de configuración.

En Excepciones debe aparecer la misma fila en cuarentena. Esto demuestra que el rechazo es visible y trazable.

### Paso 4 — Idempotencia

Volver a ejecutar exactamente la misma fuente sin modificar el CSV. Debe aparecer FILE_UNCHANGED o una ejecución equivalente sin nuevos inserts. No deben duplicarse las dos filas válidas.

Para probar un cambio, editar una copia del CSV, cambiar un Amount válido y volver a ejecutar. La aplicación debe detectar el archivo nuevo y mostrar la diferencia según INCREMENTAL_UPSERT.

### Paso 5 — Schedule

Si se creó el schedule:

1. Ir a Configuración o a la tarjeta del schedule.
2. Confirmar la expresión CRON y el timezone.
3. Esperar el siguiente minuto; el historial debe mostrar la ejecución automática.
4. Pulsar Pausar y comprobar estado INACTIVE.
5. Pulsar Activar y comprobar estado ACTIVE.
6. Al terminar la demostración, dejarlo pausado para no generar ejecuciones innecesarias.

### Paso 6 — Explorer PostgreSQL

En Explorador registrar una conexión local de desarrollo:

| Campo | Valor |
|---|---|
| Motor | PostgreSQL |
| Host | 127.0.0.1 |
| Puerto | 5432 |
| Base de datos | kiriox |
| Usuario | kiriox |
| Contraseña | kiriox |
| Schema inicial | public |

Pulsar Probar y guardar conexión. Después:

1. Comprobar discovery de schemas.
2. Elegir un schema y comprobar tablas.
3. Elegir una tabla y comprobar columnas.
4. Ejecutar preview limitado.
5. Pulsar Crear fuente desde tabla.
6. Ejecutar extracción.
7. Abrir el historial y comprobar watermark antes/después.
8. Ejecutar una segunda extracción sin cambios; debe leer cero filas nuevas.

Las credenciales anteriores son las del docker-compose.yml y son exclusivamente para desarrollo local. Deben cambiarse antes de cualquier uso real.

### Paso 7 — API y documentación

Abrir http://127.0.0.1:8000/docs y probar, en este orden, los endpoints principales:

- GET /health;
- GET /api/sources;
- POST /api/preview;
- POST /api/sources;
- POST /api/sources/{id}/preview;
- POST /api/sources/{id}/rules;
- POST /api/sources/{id}/runs;
- GET /api/sources/{id}/runs;
- GET /api/runs/{run_id};
- GET /api/runs/{run_id}/exceptions.

## 4. Pestañas de la aplicación

- **Fuentes de datos:** alta, configuración, preview y ejecución.
- **Historial de ejecuciones:** métricas, estados, watermark, errores y snapshots.
- **Excepciones:** cuarentena y detalle de registros rechazados.
- **Configuración:** timezone, tamaño de lote y telemetría.
- **Explorador:** conexión PostgreSQL, schemas, tablas, columnas, preview y creación de fuente.

## 5. Pruebas técnicas realizadas

| Verificación | Resultado |
|---|---|
| Backend | 15 pruebas pasadas |
| Ruff | PASS |
| TypeScript/lint frontend | PASS |
| Build frontend | PASS |
| Playwright E2E | 2 pruebas pasadas |
| npm audit --audit-level=high | 0 vulnerabilidades |
| E2E archivo desde la UI | 3 leídos, 2 insertados, 1 rechazado |
| E2E PostgreSQL real | conexión, discovery, preview, extracción y watermark validados |
| Repetición PostgreSQL | 0 filas nuevas en la segunda extracción |
| Schedule CRON | ejecución, pausa y activación validadas |
| Responsive | validado en 1920×1080, 1440×900 y 1366×768 |

El benchmark del reader procesó 100.000 filas a 1.114.406 filas/segundo en el equipo de desarrollo. Es una referencia de lectura local y no constituye un SLO de producción.

## 6. Alcance pendiente

- Ejecutar E2E con servidores reales de SQL Server, MySQL/MariaDB, Oracle y Db2, además de instalar sus drivers.
- Medir throughput de PostgreSQL con un dataset grande y definir un SLO.
- Incorporar autenticación multiusuario, roles y RBAC cuando se definan proveedor de identidad y políticas.
- Reducir la deuda de tipado estricto (mypy --strict) y migrar avisos deprecados de FastAPI en un sprint técnico.

## 7. Checklist de entrega

- [ ] Crear repositorio privado en GitHub.
- [ ] Revisar git diff --cached y confirmar que no hay secretos.
- [ ] Hacer el primer commit y git push a main.
- [ ] Compartir URL del repositorio y este reporte.
- [ ] Confirmar que el receptor tiene Docker Desktop, Python 3.11+ y Node 20+.
- [ ] Entregar credenciales locales solo como datos de desarrollo, nunca como credenciales productivas.

## 8. Conclusión

El módulo está listo como MVP funcional local-first. El flujo completo —configurar fuente, previsualizar, validar, cargar, rechazar y consultar evidencia, repetir de forma idempotente, programar ejecuciones y extraer desde PostgreSQL— está implementado y validado.
