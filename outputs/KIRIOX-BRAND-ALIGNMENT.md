# Kiriox Continuous Assurance — Brand Alignment

## A. Análisis de referencias

Se tomó como referencia la landing de Kiriox: composición editorial, titulares grandes en navy, superficies claras, tarjetas redondeadas, iconografía lineal, bordes sutiles, sombras suaves y CTA primario azul con acento naranja controlado. Se eliminó la lectura visual verde del producto y se mantuvo la jerarquía funcional existente.

No se encontró un archivo oficial de logotipo dentro del frontend; por ello se conservó un wordmark tipográfico sobrio, sin inventar ni modificar un recurso de marca.

## B. Paleta implementada

- Light: `#F2F3F4`
- Light secondary: `#EBEAED`
- Deep navy: `#020035`
- Navy: `#02066F`
- Primary blue: `#2000B1`
- Orange: `#ED4B00`

Los colores de éxito, warning y error quedaron separados como colores semánticos; no se usan como identidad de marca.

## C. Design tokens

Se centralizaron colores, superficies, bordes, tipografía, espaciado, radios, sombras, focus ring y transición en `frontend/styles/tokens.css`.

Radios principales: 8, 12 y 18 px. Sombra base: suave y de baja elevación. Focus ring: azul primario con contraste visible.

## D. Tipografía

Se utiliza una sans de sistema con prioridad Inter y fallback a Segoe UI/Arial. Los titulares usan peso fuerte y escala editorial responsive. Las etiquetas técnicas, IDs, estados y valores operativos usan una mono de sistema para reforzar trazabilidad.

## E. Componentes refactorizados

- AppShell y navegación responsive con iconos Lucide.
- PageHeader, Card, Button, StatusBadge, EmptyState y LoadingState.
- Stepper de configuración guiada.
- MetricCard para resumen operativo.
- DataTable para fuentes, ejecuciones, excepciones y previews.
- System status card y estados de conexión.

## F. Pantallas actualizadas

- Fuentes de datos: catálogo priorizado, métricas y creación guiada.
- Crear una fuente: flujo visual de 8 pasos, conservando la funcionalidad actual.
- Explorador PostgreSQL: extracción read-only diferenciada del flujo FILE.
- Historial de ejecuciones: métricas, estado, filtro por fuente y resultados reales.
- Excepciones: búsqueda y empty state orientado a investigación.
- Schedules: formulario de automatización y schedules persistidos.
- Configuración: resumen de valores operativos y telemetría local.

## G. Cambios UX

La navegación separa adquisición, exploración, evidencia y control operativo. El flujo de fuentes ahora comienza por el catálogo y lleva la creación a una pantalla dedicada. FILE y POSTGRESQL presentan controles específicos para evitar confusión. Los estados vacíos explican el siguiente paso y los datos operativos mantienen su contexto visible.

## H. Responsive

- 1920×1080: PASS — 9 filas visibles y sin overflow horizontal.
- 1440×900: PASS — 7 filas visibles y sin overflow horizontal.
- 1366×768: PASS — 5 filas visibles y sin overflow horizontal.

La vista mobile también fue inspeccionada y pasó: navegación horizontal accesible, grids colapsables, formularios apilados y tablas contenidas.

## I. Accessibility

Se añadieron iconos con propósito visual consistente, labels visibles en formularios, estados textuales además de color, focus ring, botones semánticos y navegación mobile con nombres accesibles. La validación visual se realizó mediante el árbol de accesibilidad del navegador local.

## J. Tests

- Frontend: 2/2 — lint/typecheck y build.
- Backend: 11/11 — pytest.
- E2E: 6/6 — revisión manual de flujos y pantallas locales; no hay suite Playwright automatizada.
- Lint: PASS.
- TypeScript: PASS.
- Build: PASS.
- Dependencias: 0 vulnerabilidades reportadas por `npm audit`.
- Ruff: PASS.

## K. Regresiones

No se modificaron backend, API, contratos, persistencia, lógica de ejecución ni tests funcionales. La actualización se limitó a `frontend/app/page.tsx`, `frontend/app/styles.css`, `frontend/components/AppShell.tsx` y `frontend/styles/tokens.css`. No se detectaron regresiones funcionales durante la revisión local.

## L. Rutas para revisar

- UI: `http://127.0.0.1:3000/`
- API docs: `http://127.0.0.1:8000/docs`
- API health: `http://127.0.0.1:8000/health`
- Vistas revisadas: Fuentes, creación guiada, Explorador PostgreSQL, Historial, Excepciones, Schedules y Configuración.
