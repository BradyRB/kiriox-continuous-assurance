from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine, URL

class ConnectorError(RuntimeError):
    pass

def safe_identifier(value: str) -> sql.Identifier:
    if not value or "\x00" in value or len(value) > 255:
        raise ValueError("Identificador SQL inválido")
    return sql.Identifier(value)

class BaseConnector:
    def connect(self) -> None: raise NotImplementedError
    def test_connection(self) -> dict[str, Any]: raise NotImplementedError
    def get_schemas(self) -> list[str]: raise NotImplementedError
    def get_tables(self, schema: str) -> list[dict[str, Any]]: raise NotImplementedError
    def get_columns(self, schema: str, table: str) -> list[dict[str, Any]]: raise NotImplementedError
    def preview(self, schema: str, table: str, limit: int = 100) -> list[dict[str, Any]]: raise NotImplementedError
    def extract(self, schema: str, table: str, watermark: dict[str, Any] | None = None, batch_size: int = 5000) -> Iterator[dict[str, Any]]: raise NotImplementedError
    def close(self) -> None: raise NotImplementedError

class PostgreSQLConnector(BaseConnector):
    """PostgreSQL source adapter. All source transactions are read-only."""
    def __init__(self, config: dict[str, Any], password: str):
        self.config = config; self.password = password; self.connection: psycopg.Connection | None = None

    def connect(self) -> None:
        try:
            self.connection = psycopg.connect(host=self.config["host"], port=int(self.config.get("port", 5432)), dbname=self.config["database"], user=self.config["username"], password=self.password, sslmode=self.config.get("sslmode", "prefer"), row_factory=dict_row, options="-c default_transaction_read_only=on")
        except psycopg.Error as exc:
            raise ConnectorError(self._safe_error(exc)) from exc

    def _require_connection(self) -> psycopg.Connection:
        if self.connection is None or self.connection.closed: self.connect()
        assert self.connection is not None
        return self.connection

    @staticmethod
    def _safe_error(exc: Exception) -> str:
        text = str(exc)
        for marker in ("password=", "user=", "passfile=", "sslkey="):
            if marker in text: text = text.split(marker, 1)[0].rstrip(" ,")
        return text[:500]

    def test_connection(self) -> dict[str, Any]:
        conn = self._require_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT current_database() AS database, current_user AS username, version() AS version")
            result = cur.fetchone() or {}
        return {"database": result.get("database"), "username": result.get("username"), "version": str(result.get("version", "")).split(",", 1)[0]}

    def get_schemas(self) -> list[str]:
        with self._require_connection().cursor() as cur:
            cur.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT LIKE 'pg_%' AND schema_name <> 'information_schema' ORDER BY schema_name")
            return [row["schema_name"] for row in cur.fetchall()]

    def get_tables(self, schema: str) -> list[dict[str, Any]]:
        with self._require_connection().cursor() as cur:
            cur.execute("SELECT table_name, table_type FROM information_schema.tables WHERE table_schema = %s ORDER BY table_name", (schema,)); return list(cur.fetchall())

    def get_columns(self, schema: str, table: str) -> list[dict[str, Any]]:
        with self._require_connection().cursor() as cur:
            cur.execute("SELECT column_name, data_type, is_nullable, ordinal_position FROM information_schema.columns WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position", (schema, table)); return list(cur.fetchall())

    def preview(self, schema: str, table: str, limit: int = 100) -> list[dict[str, Any]]:
        if not 1 <= limit <= 100: raise ValueError("El preview debe estar entre 1 y 100 filas")
        query = sql.SQL("SELECT * FROM {}.{} LIMIT %s").format(safe_identifier(schema), safe_identifier(table))
        with self._require_connection().cursor() as cur:
            cur.execute(query, (limit,)); return list(cur.fetchall())

    def extract(self, schema: str, table: str, watermark: dict[str, Any] | None = None, batch_size: int = 5000) -> Iterator[dict[str, Any]]:
        if batch_size < 1: raise ValueError("batch_size debe ser positivo")
        conn = self._require_connection(); wm = watermark or {}; column = wm.get("column"); primary_key = wm.get("primary_key")
        query = sql.SQL("SELECT * FROM {}.{}").format(safe_identifier(schema), safe_identifier(table)); params: list[Any] = []
        if column:
            if primary_key and "value" in wm:
                query += sql.SQL(" WHERE ({} > %s) OR ({} = %s AND {} > %s)").format(safe_identifier(column), safe_identifier(column), safe_identifier(primary_key)); params.extend([wm["value"], wm["value"], wm.get("primary_key_value")])
            elif "value" in wm:
                query += sql.SQL(" WHERE {} > %s").format(safe_identifier(column)); params.append(wm["value"])
        if column:
            query += sql.SQL(" ORDER BY {} ASC").format(safe_identifier(column))
            if primary_key: query += sql.SQL(", {} ASC").format(safe_identifier(primary_key))
        with conn.cursor(name="kiriox_source_stream", row_factory=dict_row) as cur:
            cur.execute(query, params)
            while rows := cur.fetchmany(batch_size): yield from rows

    def close(self) -> None:
        if self.connection is not None and not self.connection.closed: self.connection.close()

PostgreSQLSourceConnector = PostgreSQLConnector


class SQLAlchemyConnector(BaseConnector):
    """Read-only adapter for engines supported by SQLAlchemy dialects.

    The application only emits SELECT statements. The operator must still grant
    the source credential read-only permissions because other engines do not
    expose one portable transaction-level read-only switch.
    """

    DIALECTS = {"SQLSERVER": "mssql+pyodbc", "MYSQL": "mysql+pymysql", "MARIADB": "mariadb+mariadbconnector", "ORACLE": "oracle+oracledb", "DB2": "ibm_db_sa"}

    def __init__(self, config: dict[str, Any], password: str):
        self.config = config; self.password = password; self.engine: Engine | None = None

    def _url(self) -> URL:
        engine = str(self.config.get("engine", "")).upper()
        dialect = self.DIALECTS.get(engine)
        if not dialect: raise ConnectorError(f"Motor no soportado: {engine or 'desconocido'}")
        query: dict[str, str] = {}
        if engine == "SQLSERVER": query["driver"] = self.config.get("driver", "ODBC Driver 18 for SQL Server")
        if engine == "ORACLE": return URL.create(dialect, username=self.config["username"], password=self.password, host=self.config["host"], port=int(self.config.get("port", 1521)), database=self.config["database"])
        return URL.create(dialect, username=self.config["username"], password=self.password, host=self.config["host"], port=int(self.config["port"]), database=self.config["database"], query=query)

    def connect(self) -> None:
        try:
            self.engine = create_engine(self._url(), pool_pre_ping=True)
            with self.engine.connect() as connection: connection.execute(text("SELECT 1"))
        except Exception as exc:
            self.close(); raise ConnectorError(self._safe_error(exc)) from exc

    def _require_engine(self) -> Engine:
        if self.engine is None: self.connect()
        assert self.engine is not None
        return self.engine

    @staticmethod
    def _safe_error(exc: Exception) -> str:
        message = str(exc)
        for marker in ("password=", "user=", "PWD=", "UID="): 
            if marker in message: message = message.split(marker, 1)[0].rstrip(" ,;")
        return message[:500]

    def _quote(self, value: str) -> str:
        if not value or "\x00" in value or len(value) > 255: raise ValueError("Identificador SQL inválido")
        return self._require_engine().dialect.identifier_preparer.quote(value)

    def test_connection(self) -> dict[str, Any]:
        engine = self._require_engine()
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 AS connected")).mappings().one()
        return {"database": self.config.get("database"), "username": self.config.get("username"), "version": f"{engine.dialect.name} · connected={result['connected']}"}

    def get_schemas(self) -> list[str]:
        names = inspect(self._require_engine()).get_schema_names()
        hidden = {"information_schema", "sys", "pg_catalog", "mysql", "performance_schema", "db2inst1"}
        return sorted(name for name in names if name.lower() not in hidden)

    def get_tables(self, schema: str) -> list[dict[str, Any]]:
        inspector = inspect(self._require_engine()); names = set(inspector.get_table_names(schema=schema))
        names.update(inspector.get_view_names(schema=schema))
        return [{"table_name": name, "table_type": "VIEW" if name in inspector.get_view_names(schema=schema) else "TABLE"} for name in sorted(names)]

    def get_columns(self, schema: str, table: str) -> list[dict[str, Any]]:
        columns = inspect(self._require_engine()).get_columns(table, schema=schema)
        return [{"column_name": str(column["name"]), "data_type": str(column.get("type", "")), "is_nullable": "YES" if column.get("nullable", True) else "NO", "ordinal_position": index} for index, column in enumerate(columns, 1)]

    def _limited_query(self, schema: str, table: str, limit: int) -> str:
        qualified = f"{self._quote(schema)}.{self._quote(table)}"; dialect = self._require_engine().dialect.name
        if dialect == "mssql": return f"SELECT TOP {limit} * FROM {qualified}"
        suffix = f"FETCH FIRST {limit} ROWS ONLY" if dialect in {"oracle", "ibm_db_sa"} else f"LIMIT {limit}"
        return f"SELECT * FROM {qualified} {suffix}"

    def preview(self, schema: str, table: str, limit: int = 100) -> list[dict[str, Any]]:
        if not 1 <= limit <= 100: raise ValueError("El preview debe estar entre 1 y 100 filas")
        with self._require_engine().connect() as connection: return [dict(row) for row in connection.execute(text(self._limited_query(schema, table, limit))).mappings().all()]

    def extract(self, schema: str, table: str, watermark: dict[str, Any] | None = None, batch_size: int = 5000) -> Iterator[dict[str, Any]]:
        if batch_size < 1: raise ValueError("batch_size debe ser positivo")
        config = watermark or {}; column = config.get("column"); primary_key = config.get("primary_key"); qualified = f"{self._quote(schema)}.{self._quote(table)}"; query = f"SELECT * FROM {qualified}"; params: dict[str, Any] = {}
        if column:
            quoted_column = self._quote(column); query += f" WHERE {quoted_column} > :watermark_value"; params["watermark_value"] = config.get("value")
            if primary_key:
                quoted_key = self._quote(primary_key); query = query.rsplit(" WHERE ", 1)[0] + f" WHERE ({quoted_column} > :watermark_value) OR ({quoted_column} = :watermark_value AND {quoted_key} > :watermark_primary_key)"; params["watermark_primary_key"] = config.get("primary_key_value")
            query += f" ORDER BY {quoted_column} ASC" + (f", {self._quote(primary_key)} ASC" if primary_key else "")
        with self._require_engine().connect().execution_options(stream_results=True) as connection:
            result = connection.execute(text(query), params)
            while rows := result.mappings().fetchmany(batch_size): yield from (dict(row) for row in rows)

    def close(self) -> None:
        if self.engine is not None: self.engine.dispose(); self.engine = None
