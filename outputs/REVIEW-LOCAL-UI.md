# Revisión local de Kiriox Continuous Assurance

Fecha: 2026-09-14

## Resultado

La aplicación quedó ejecutándose y accesible en el navegador local. Se revisaron los flujos principales con PostgreSQL local activo.

## Pasos revisados

1. Fuentes de datos — saludable. La lista carga nueve fuentes y el wizard muestra estados vacíos, selección y validation builder.
2. Explorador PostgreSQL — saludable. El estado vacío explica que la conexión debe verificarse; la pantalla incluye formulario read-only y luego consulta schemas, tablas, columnas y preview.
3. Historial de ejecuciones — saludable. El estado vacío funciona y una fuente real muestra métricas, estados y acciones de excepciones.
4. Excepciones — saludable. El estado vacío explica cómo llegar desde un run.
5. Schedules — saludable. Se muestran frecuencias, timezone, formulario y schedules persistidos.
6. Configuración — saludable. Expone timezone, batch size y telemetría desactivada.
7. Operación PostgreSQL — corregido durante esta revisión. Una fuente PostgreSQL muestra extracción read-only y watermark; no presenta controles de archivo.
8. Responsive — aceptable en la vista móvil disponible. Se añadió navegación horizontal para conservar acceso a todas las pantallas.

## Hallazgos

- Corregido: controles de archivo visibles para fuentes PostgreSQL.
- Sin errores visibles de carga, pantalla en blanco o backend caído.
- La comparación específica a 1366px y 1440px+ todavía requiere una captura instrumental dedicada.
- No se subieron archivos desde la interfaz durante esta revisión; las pruebas de archivos ya se ejecutaron por API/pipeline.

## Evidencia técnica

- PostgreSQL: `healthy`, `pg_isready` aceptando conexiones.
- API: `/health` devuelve `status=ok`; `/docs` devuelve HTTP 200.
- UI: HTTP 200 en `127.0.0.1:3000`.
- Backend: `pytest` 11/11 y Ruff sin hallazgos.
- Frontend: typecheck, build y `npm audit` sin vulnerabilidades.
