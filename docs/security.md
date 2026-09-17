# Seguridad

El servicio enlaza a `127.0.0.1` por defecto. La master key vive en `KIRIOX_MASTER_KEY`, nunca en PostgreSQL ni Git. Los secretos se cifran antes de persistir y no se devuelven a la UI. Los errores del connector se recortan y limpian antes de persistirse. Las cuentas de origen deben ser read-only; `PostgreSQLConnector` fuerza `default_transaction_read_only=on` y no incluye operaciones de escritura sobre las fuentes auditadas.

Para SQL Server, MySQL/MariaDB, Oracle y Db2, el adapter solo genera operaciones `SELECT`; el operador debe crear credenciales de solo lectura en el motor porque no existe una bandera portable de transacción read-only. En producción sustituir el valor devuelto por `.env.example` por un secreto local gestionado por el operador y rotarlo con procedimiento documentado.
