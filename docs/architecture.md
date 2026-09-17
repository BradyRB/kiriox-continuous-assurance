# Arquitectura

Kiriox es local-first: los archivos y conexiones se procesan en el equipo donde se despliega el backend. El frontend solo invoca la API local. PostgreSQL mantiene cuatro dominios: `ingestion` (configuración y runs), `raw` (evidencia recibida y cuarentena), `data` (registros aprobados) y `audit` (eventos).

El pipeline tiene seis fronteras: `FileReader`/`BaseConnector`, extracción iterativa, detección por hash, `Validation Engine`, loader transaccional y registro de evidencia. Los lectores trabajan como iteradores; XLSX usa `read_only=True`, XML usa `iterparse`, y CSV/TXT no materializan el archivo. PostgreSQL usa psycopg y los motores SQL adicionales usan `SQLAlchemyConnector` con drivers opcionales.

Una ejecución crea primero su evidencia operativa, toma un advisory lock por `data_source_id`, valida en streaming y confirma datos válidos, raw y cuarentena en una única transacción. Un fallo técnico hace rollback del lote y registra `FAILED`; un fallo de calidad conserva válidos y marca `COMPLETED_WITH_ERRORS`.
