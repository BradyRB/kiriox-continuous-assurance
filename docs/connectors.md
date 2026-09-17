# Conectores

El contrato es `BaseConnector`: `connect`, `test_connection`, `get_schemas`, `get_tables`, `get_columns`, `preview`, `extract` y `close`. `PostgreSQLConnector` está implementado con psycopg, `default_transaction_read_only=on`, identifiers construidos con `psycopg.sql.Identifier`, valores parametrizados, preview máximo de 100 filas y cursor nombrado con `fetchmany`.

La extracción incremental usa `(watermark_column, primary_key)` cuando ambos están configurados: filtra por timestamp mayor o, en empate, por primary key mayor; ordena por ambos. El estado confirmado se guarda en `ingestion.watermarks` solo dentro de la transacción de carga local.

SQL Server, MySQL/MariaDB, Oracle y Db2 usan el adapter `SQLAlchemyConnector`, con dialectos y drivers opcionales definidos en `backend/requirements-connectors.txt`. La API puede registrar esos motores y ejecuta únicamente discovery, preview y extracción `SELECT`; el driver y la instancia deben existir en el entorno del operador. Si falta un driver, la conexión falla explícitamente y no se falsifican resultados.

Drivers:

- SQL Server: `pyodbc` y un ODBC Driver instalado.
- MySQL: `pymysql`.
- MariaDB: `mariadb`.
- Oracle: `oracledb`.
- Db2: `ibm-db-sa` y su runtime IBM Db2.

El explorador visual actual continúa etiquetado PostgreSQL y requiere una ampliación de formulario para seleccionar estos motores desde UI; los conectores adicionales están disponibles mediante la API documentada.

V1 no permite SQL arbitrario. Las consultas de origen deben ser de lectura y aplicar límites, paginación/keyset o cursores del servidor.
