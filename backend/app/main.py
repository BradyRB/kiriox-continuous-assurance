from __future__ import annotations
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import UUID
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from .db import get_db
from .db import SessionLocal
from .models import AuditEvent, Connection, DataSource, Dataset, LoadRun, LoadRunError, QuarantineRecord, ValidationRule
from .connectors import BaseConnector, PostgreSQLConnector, SQLAlchemyConnector
from .security import secret_box
from .pipeline import run_db_ingestion, run_file_ingestion
from .readers import get_reader
from .scheduler import PersistentScheduler, SCHEDULE_TYPES, is_retryable_error, next_run_at
from .schemas import ConnectionCreate, ConnectionOut, PreviewOut, RuleCreate, ScheduleCreate, SourceCreate, SourceOut
from .models import Schedule
from .validation import infer_types

app = FastAPI(title="Kiriox Continuous Assurance — Local", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"], allow_methods=["GET", "POST"], allow_headers=["*"])
STORAGE = Path(__file__).resolve().parents[1] / "storage"
_scheduler: PersistentScheduler | None = None
SUPPORTED_ENGINES = {"POSTGRESQL", "SQLSERVER", "MYSQL", "MARIADB", "ORACLE", "DB2"}

def _scheduled_run(source_id: UUID) -> None:
    with SessionLocal() as db:
        source = db.get(DataSource, source_id); dataset = db.scalar(select(Dataset).where(Dataset.data_source_id == source_id))
        if not source or not dataset: return
        if source.source_type == "FILE":
            configured_path = source.config.get("file_path")
            path = Path(configured_path) if configured_path else None
            if not path or not path.is_file():
                candidates = sorted(STORAGE.glob(f"{source_id}-*"), key=lambda item: item.stat().st_mtime, reverse=True)
                path = candidates[0] if candidates else None
            if path and path.is_file(): run = run_file_ingestion(db, source, dataset, path, path.name.removeprefix(f"{source_id}-"))
            else: return
        elif source.source_type == "POSTGRESQL":
            connector = _get_connector(source.connection_id, db)
            try: run = run_db_ingestion(db, source, dataset, connector)
            finally: connector.close()
        else: return
        if run.status == "FAILED":
            failure = db.scalar(select(LoadRunError).where(LoadRunError.run_id == run.id).order_by(LoadRunError.created_at.desc()))
            if failure and is_retryable_error(RuntimeError(failure.message)):
                raise RuntimeError(failure.message)

@app.on_event("startup")
def start_scheduler() -> None:
    global _scheduler
    _scheduler = PersistentScheduler(SessionLocal, _scheduled_run)
    _scheduler.start()

@app.on_event("shutdown")
def stop_scheduler() -> None:
    if _scheduler: _scheduler.stop()

@app.get("/health")
def health(): return {"status": "ok", "mode": "local-first"}

@app.get("/")
def root(): return {"service": "Kiriox Continuous Assurance — Local", "status": "ok", "docs": "/docs", "health": "/health"}

@app.get("/api/sources", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)): return db.scalars(select(DataSource).order_by(DataSource.name)).all()

@app.post("/api/sources", response_model=SourceOut, status_code=201)
def create_source(payload: SourceCreate, db: Session = Depends(get_db)):
    if payload.source_type not in {"FILE", "POSTGRESQL"}:
        raise HTTPException(422, "Los conectores de bases de datos se habilitarán en el sprint de conectores; no se simula una conexión")
    if payload.source_type == "POSTGRESQL" and payload.connection_id is None:
        raise HTTPException(422, "Una fuente PostgreSQL requiere connection_id")
    if payload.source_type == "POSTGRESQL" and (not payload.config.get("schema") or not payload.config.get("table")):
        raise HTTPException(422, "Una fuente PostgreSQL requiere config.schema y config.table")
    if any(key.lower() in {"password", "token", "secret", "secret_ciphertext"} for key in payload.config):
        raise HTTPException(422, "Las credenciales no se aceptan en config; deben cifrarse mediante el gestor de conexiones")
    if payload.load_mode in ("APPEND", "INCREMENTAL_UPSERT") and not payload.business_key: raise HTTPException(422, "business_key es obligatorio para este modo de carga")
    source = DataSource(name=payload.name, description=payload.description, source_type=payload.source_type, connection_id=payload.connection_id, config=payload.config)
    db.add(source); db.flush(); dataset = Dataset(data_source_id=source.id, name=payload.dataset_name, table_name=payload.table_name, load_mode=payload.load_mode, business_key=payload.business_key, columns=payload.config.get("columns", {})); db.add(dataset)
    db.add(AuditEvent(event_type="SOURCE_CREATED", actor="local-user", object_type="DATA_SOURCE", object_id=source.id, payload=payload.model_dump(mode="json"))); db.commit(); db.refresh(source); return source

@app.post("/api/connections", response_model=ConnectionOut, status_code=201)
def create_connection(payload: ConnectionCreate, db: Session = Depends(get_db)):
    engine = payload.engine.upper()
    if engine not in SUPPORTED_ENGINES: raise HTTPException(422, f"Motor no soportado: {payload.engine}")
    config = {"engine": engine, "host": payload.host, "port": payload.port, "database": payload.database, "schema": payload.schema_, "username": payload.username, "sslmode": payload.sslmode}
    connection = Connection(name=payload.name, engine=engine, config=config, secret_ciphertext=secret_box.encrypt(payload.password)); db.add(connection); db.flush(); db.add(AuditEvent(event_type="CONNECTION_CREATED", actor="local-user", object_type="CONNECTION", object_id=connection.id, payload={"name": payload.name, "engine": engine})); db.commit(); db.refresh(connection)
    return connection

def _get_connector(connection_id: UUID, db: Session) -> BaseConnector:
    connection = db.get(Connection, connection_id)
    if not connection or not connection.secret_ciphertext: raise HTTPException(404, "Conexión no encontrada")
    config = {**connection.config, "engine": connection.engine}
    return PostgreSQLConnector(config, secret_box.decrypt(connection.secret_ciphertext)) if connection.engine == "POSTGRESQL" else SQLAlchemyConnector(config, secret_box.decrypt(connection.secret_ciphertext))

@app.post("/api/connections/{connection_id}/test")
def test_connection(connection_id: UUID, db: Session = Depends(get_db)):
    connector = _get_connector(connection_id, db)
    try: return {"status": "CONNECTED", **connector.test_connection()}
    except Exception as exc: raise HTTPException(502, {"error_code": "CONNECTION_FAILED", "message": str(exc)[:500]}) from exc
    finally: connector.close()

@app.get("/api/connections/{connection_id}/schemas")
def connection_schemas(connection_id: UUID, db: Session = Depends(get_db)):
    connector = _get_connector(connection_id, db)
    try: return connector.get_schemas()
    finally: connector.close()

@app.get("/api/connections/{connection_id}/objects")
def connection_objects(connection_id: UUID, schema: str, db: Session = Depends(get_db)):
    connector = _get_connector(connection_id, db)
    try: return connector.get_tables(schema)
    finally: connector.close()

@app.get("/api/connections/{connection_id}/columns")
def connection_columns(connection_id: UUID, schema: str, table: str, db: Session = Depends(get_db)):
    connector = _get_connector(connection_id, db)
    try: return connector.get_columns(schema, table)
    finally: connector.close()

@app.get("/api/connections/{connection_id}/preview")
def connection_preview(connection_id: UUID, schema: str, table: str, limit: int = 100, db: Session = Depends(get_db)):
    connector = _get_connector(connection_id, db)
    try: return connector.preview(schema, table, limit)
    finally: connector.close()

@app.post("/api/sources/{source_id}/rules", status_code=201)
def create_rule(source_id: UUID, payload: RuleCreate, db: Session = Depends(get_db)):
    dataset = db.scalar(select(Dataset).where(Dataset.data_source_id == source_id))
    if not dataset: raise HTTPException(404, "Dataset no encontrado")
    rule = ValidationRule(dataset_id=dataset.id, **payload.model_dump()); db.add(rule); db.commit(); return {"id": str(rule.id), **payload.model_dump()}

@app.post("/api/sources/{source_id}/preview", response_model=PreviewOut)
def preview(source_id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db)):
    source = db.get(DataSource, source_id)
    if not source: raise HTTPException(404, "Fuente no encontrada")
    STORAGE.mkdir(exist_ok=True); suffix = Path(file.filename or "upload.csv").suffix; temp = NamedTemporaryFile(delete=False, suffix=suffix, dir=STORAGE); temp.close()
    with open(temp.name, "wb") as out: shutil.copyfileobj(file.file, out)
    try:
        profile = get_reader(file.filename or "upload.csv").profile(Path(temp.name), source.config.get("reader_options", {}))
        return PreviewOut(columns=profile.columns, preview=profile.preview, rows_estimated=profile.rows_estimated, inferred_types=infer_types(profile.preview))
    finally: Path(temp.name).unlink(missing_ok=True)

@app.post("/api/preview", response_model=PreviewOut)
def preview_upload(file: UploadFile = File(...), reader_options: str = Form("{}")):
    """Profile an upload before a source is persisted; the temporary file is always removed."""
    try:
        options = json.loads(reader_options)
        if not isinstance(options, dict): raise ValueError("reader_options debe ser un objeto JSON")
    except (TypeError, json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(422, "reader_options inválido") from exc
    try: options["preview_rows"] = min(max(int(options.get("preview_rows", 10)), 1), 100)
    except (TypeError, ValueError) as exc: raise HTTPException(422, "preview_rows inválido") from exc
    STORAGE.mkdir(exist_ok=True); suffix = Path(file.filename or "upload.csv").suffix; temp = NamedTemporaryFile(delete=False, suffix=suffix, dir=STORAGE); temp.close()
    with open(temp.name, "wb") as out: shutil.copyfileobj(file.file, out)
    try:
        profile = get_reader(file.filename or "upload.csv").profile(Path(temp.name), options)
        return PreviewOut(columns=profile.columns, preview=profile.preview, rows_estimated=profile.rows_estimated, inferred_types=infer_types(profile.preview))
    except (ValueError, KeyError) as exc:
        raise HTTPException(422, str(exc)) from exc
    finally: Path(temp.name).unlink(missing_ok=True)

@app.post("/api/sources/{source_id}/runs")
def run_source(source_id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db)):
    source = db.get(DataSource, source_id); dataset = db.scalar(select(Dataset).where(Dataset.data_source_id == source_id))
    if not source or not dataset: raise HTTPException(404, "Fuente o dataset no encontrado")
    STORAGE.mkdir(exist_ok=True); safe_name = Path(file.filename or "upload.csv").name; path = STORAGE / f"{source_id}-{safe_name}"
    with path.open("wb") as out: shutil.copyfileobj(file.file, out)
    run = run_file_ingestion(db, source, dataset, path, safe_name)
    return {"id": str(run.id), "status": run.status, "rows_read": run.rows_read, "rows_inserted": run.rows_inserted, "rows_updated": run.rows_updated, "rows_unchanged": run.rows_unchanged, "rows_rejected": run.rows_rejected, "warning_count": run.warning_count, "error_count": run.error_count}

@app.post("/api/sources/{source_id}/db-runs")
def run_database_source(source_id: UUID, db: Session = Depends(get_db)):
    source = db.get(DataSource, source_id); dataset = db.scalar(select(Dataset).where(Dataset.data_source_id == source_id))
    if not source or not dataset or source.source_type != "POSTGRESQL": raise HTTPException(404, "Fuente PostgreSQL no encontrada")
    connector = _get_connector(source.connection_id, db)
    try:
        run = run_db_ingestion(db, source, dataset, connector)
        return {"id": str(run.id), "status": run.status, "rows_read": run.rows_read, "rows_inserted": run.rows_inserted, "rows_updated": run.rows_updated, "rows_unchanged": run.rows_unchanged, "rows_rejected": run.rows_rejected, "watermark_before": run.watermark_before, "watermark_after": run.watermark_after}
    finally: connector.close()

@app.post("/api/schedules", status_code=201)
def create_schedule(payload: ScheduleCreate, db: Session = Depends(get_db)):
    if payload.schedule_type not in SCHEDULE_TYPES: raise HTTPException(422, "schedule_type inválido")
    now = datetime.now(timezone.utc); schedule = Schedule(**payload.model_dump(), next_run_at=next_run_at(payload.schedule_type, now, payload.timezone, hour=payload.hour, minute=payload.minute, interval_hours=payload.interval_hours, day_of_week=payload.day_of_week, day_of_month=payload.day_of_month, cron_expression=payload.cron_expression)); db.add(schedule); db.commit(); db.refresh(schedule); return {"id": str(schedule.id), "next_run_at": schedule.next_run_at, "enabled": schedule.enabled, "schedule_type": schedule.schedule_type}

@app.get("/api/schedules")
def list_schedules(db: Session = Depends(get_db)):
    return [{"id": str(s.id), "data_source_id": str(s.data_source_id), "schedule_type": s.schedule_type, "timezone": s.timezone, "enabled": s.enabled, "next_run_at": s.next_run_at, "last_run_at": s.last_run_at, "retry_count": s.retry_count} for s in db.scalars(select(Schedule).order_by(Schedule.next_run_at)).all()]

@app.post("/api/schedules/{schedule_id}/toggle")
def toggle_schedule(schedule_id: UUID, db: Session = Depends(get_db)):
    schedule = db.get(Schedule, schedule_id)
    if not schedule: raise HTTPException(404, "Schedule no encontrado")
    schedule.enabled = not schedule.enabled; db.commit(); return {"id": str(schedule.id), "enabled": schedule.enabled}

@app.get("/api/sources/{source_id}/runs")
def history(source_id: UUID, db: Session = Depends(get_db)):
    runs = db.scalars(select(LoadRun).where(LoadRun.data_source_id == source_id).order_by(desc(LoadRun.started_at))).all()
    return [{k: getattr(run, k) for k in ("id","started_at","finished_at","status","rows_read","rows_inserted","rows_updated","rows_unchanged","rows_rejected","error_count","warning_count")} | {"id": str(run.id)} for run in runs]

@app.get("/api/runs/{run_id}/exceptions")
def exceptions(run_id: UUID, db: Session = Depends(get_db)):
    return [{"id": str(x.id), "row_number": x.row_number, "column": x.column_name, "value": x.value, "rule": x.rule, "error_code": x.error_code, "message": x.error_message, "raw_record": x.raw_record} for x in db.scalars(select(QuarantineRecord).where(QuarantineRecord.run_id == run_id).order_by(QuarantineRecord.row_number)).all()]

@app.get("/api/runs/{run_id}")
def run_detail(run_id: UUID, db: Session = Depends(get_db)):
    run = db.get(LoadRun, run_id)
    if not run: raise HTTPException(404, "Ejecución no encontrada")
    source = db.get(DataSource, run.data_source_id)
    errors = db.scalars(select(LoadRunError).where(LoadRunError.run_id == run.id).order_by(LoadRunError.created_at)).all()
    quarantined = db.scalars(select(QuarantineRecord).where(QuarantineRecord.run_id == run.id).order_by(QuarantineRecord.row_number)).all()
    return {
        "id": str(run.id), "source_id": str(run.data_source_id), "source_name": source.name if source else None,
        "started_at": run.started_at, "finished_at": run.finished_at, "status": run.status,
        "rows_read": run.rows_read, "rows_inserted": run.rows_inserted, "rows_updated": run.rows_updated,
        "rows_unchanged": run.rows_unchanged, "rows_rejected": run.rows_rejected, "error_count": run.error_count,
        "warning_count": run.warning_count, "watermark_before": run.watermark_before, "watermark_after": run.watermark_after,
        "configuration_snapshot": run.configuration_snapshot,
        "errors": [{"id": str(item.id), "type": item.error_type, "message": item.message, "created_at": item.created_at} for item in errors],
        "exceptions": [{"id": str(item.id), "row_number": item.row_number, "column": item.column_name, "value": item.value, "rule": item.rule, "error_code": item.error_code, "message": item.error_message, "raw_record": item.raw_record} for item in quarantined],
    }
