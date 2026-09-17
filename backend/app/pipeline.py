from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from uuid import UUID

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from .hashing import file_sha256, row_hash
from .models import AuditEvent, DataRecord, Dataset, FileVersion, LoadRun, LoadRunError, QuarantineRecord, RawRecord, ValidationRule, Watermark
from .readers import get_reader
from .validation import validate_row

logger = logging.getLogger("kiriox.pipeline")

def _json_safe(value: Any) -> Any:
    if isinstance(value, dict): return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [_json_safe(v) for v in value]
    if isinstance(value, UUID): return str(value)
    if hasattr(value, "isoformat"): return value.isoformat()
    if hasattr(value, "as_tuple"): return format(value, "f")
    return value

def _finish_failed(db: Session, run: LoadRun, exc: Exception) -> LoadRun:
    run_id = run.id
    metrics = {name: getattr(run, name) for name in ("rows_read", "rows_inserted", "rows_updated", "rows_unchanged", "rows_rejected", "error_count", "warning_count")}
    watermark_before = run.watermark_before
    configuration_snapshot = run.configuration_snapshot
    db.rollback(); failed = db.get(LoadRun, run_id)
    assert failed is not None
    failed.status = "FAILED"; failed.finished_at = datetime.now(timezone.utc); failed.watermark_before = watermark_before; failed.configuration_snapshot = configuration_snapshot
    for name, value in metrics.items(): setattr(failed, name, value)
    failed.error_count = max(1, failed.error_count)
    db.add(LoadRunError(run_id=run_id, error_type="TECHNICAL", message=str(exc)[:1000])); db.commit(); db.refresh(failed)
    return failed

def _try_source_lock(db: Session, source_id: Any) -> bool:
    try:
        return bool(db.scalar(select(text("pg_try_advisory_xact_lock(hashtextextended(:key, 0))")).params(key=str(source_id))))
    except Exception:
        db.rollback(); logger.warning("Advisory lock unavailable; PostgreSQL is required for production execution")
        return True

def _rules_snapshot(db: Session, dataset_id: Any) -> list[dict[str, Any]]:
    return [dict(column_name=r.column_name, rule_type=r.rule_type, rule_config=r.rule_config, severity=r.severity, enabled=r.enabled) for r in db.scalars(select(ValidationRule).where(ValidationRule.dataset_id == dataset_id)).all()]

def _process_stream(db: Session, run: LoadRun, dataset: Dataset, records: Iterable[dict[str, Any]], rules: list[dict[str, Any]], batch_size: int) -> tuple[dict[str, Any] | None, dict[str, set[str]]]:
    seen: dict[str, set[str]] = {}; raw_batch: list[RawRecord] = []; last_record: dict[str, Any] | None = None
    for row_number, record in enumerate(records, 1):
        last_record = record; safe_record = _json_safe(record); digest_row = row_hash(record); run.rows_read += 1
        raw_batch.append(RawRecord(run_id=run.id, row_number=row_number, record=safe_record, row_hash=digest_row))
        issues = validate_row(record, rules, seen); errors = [issue for issue in issues if issue.severity == "ERROR"]
        run.warning_count += sum(issue.severity == "WARNING" for issue in issues); run.rows_rejected += 1 if errors else 0
        for issue in issues:
            db.add(QuarantineRecord(run_id=run.id, dataset_id=dataset.id, dataset=dataset.name, row_number=row_number, business_key={key: _json_safe(record.get(key)) for key in dataset.business_key} if dataset.business_key else None, raw_record=safe_record, column_name=issue.column, value=issue.value, rule=issue.rule, error_code=issue.code, error_message=issue.message))
        if not errors:
            if dataset.load_mode == "FULL_REPLACE": key_payload, key_columns = {"_source_row": row_number}, ["_source_row"]
            else:
                if not dataset.business_key: raise ValueError("INCREMENTAL_UPSERT/APPEND requiere business_key para evitar duplicados silenciosos")
                key_payload, key_columns = {key: record.get(key) for key in dataset.business_key}, dataset.business_key
            key_digest = row_hash(key_payload, key_columns); existing = db.scalar(select(DataRecord).where(DataRecord.dataset_id == dataset.id, DataRecord.business_key_hash == key_digest).with_for_update())
            if existing is None: db.add(DataRecord(dataset_id=dataset.id, run_id=run.id, business_key_hash=key_digest, row_hash=digest_row, record=safe_record)); run.rows_inserted += 1
            elif existing.row_hash == digest_row: run.rows_unchanged += 1
            else: existing.row_hash, existing.record, existing.run_id = digest_row, safe_record, run.id; run.rows_updated += 1
        if len(raw_batch) >= batch_size: db.add_all(raw_batch); db.flush(); raw_batch.clear()
    if raw_batch: db.add_all(raw_batch)
    return last_record, seen

def _finish_success(db: Session, run: LoadRun, actor: str, payload: dict[str, Any]) -> LoadRun:
    run.finished_at = datetime.now(timezone.utc); run.status = "COMPLETED_WITH_ERRORS" if run.rows_rejected else ("COMPLETED_WITH_WARNINGS" if run.warning_count else "COMPLETED")
    db.add(AuditEvent(event_type="EXECUTION_COMPLETED", actor=actor, object_type="LOAD_RUN", object_id=run.id, payload=payload)); db.commit(); db.refresh(run)
    return run

def run_file_ingestion(db: Session, source, dataset: Dataset, path: Path, filename: str, actor: str = "local-user") -> LoadRun:
    digest = file_sha256(path); existing = db.scalar(select(FileVersion).where(FileVersion.data_source_id == source.id, FileVersion.sha256 == digest))
    run = LoadRun(data_source_id=source.id, configuration_snapshot={"source": source.config, "dataset": {"name": dataset.name, "load_mode": dataset.load_mode, "business_key": dataset.business_key}}); db.add(run); db.commit(); db.refresh(run)
    try:
        rules = _rules_snapshot(db, dataset.id); run.configuration_snapshot = {**run.configuration_snapshot, "validation_rules": rules}; db.commit()
        if existing and existing.status == "PROCESSED": run.status = "FILE_UNCHANGED"; run.finished_at = datetime.now(timezone.utc); db.commit(); return run
        if not _try_source_lock(db, source.id): run.status = "SKIPPED_ALREADY_RUNNING"; run.finished_at = datetime.now(timezone.utc); db.commit(); return run
        reader = get_reader(filename); file_version = existing or FileVersion(data_source_id=source.id, filename=filename, file_size=path.stat().st_size, sha256=digest, uploaded_by=actor, status="RECEIVED"); db.add(file_version); db.flush(); run.file_version_id = file_version.id
        batch_size = int(source.config.get("batch_size", 5000))
        if dataset.load_mode == "FULL_REPLACE": db.execute(delete(DataRecord).where(DataRecord.dataset_id == dataset.id))
        _process_stream(db, run, dataset, reader.rows(path, source.config.get("reader_options", {})), rules, batch_size)
        file_version.status, file_version.processed_at = "PROCESSED", datetime.now(timezone.utc)
        return _finish_success(db, run, actor, {"source_type": "FILE", "rows_read": run.rows_read, "inserted": run.rows_inserted, "updated": run.rows_updated, "rejected": run.rows_rejected})
    except Exception as exc: return _finish_failed(db, run, exc)

def run_db_ingestion(db: Session, source, dataset: Dataset, connector, actor: str = "local-user") -> LoadRun:
    run = LoadRun(data_source_id=source.id, configuration_snapshot={"source": source.config, "dataset": {"name": dataset.name, "load_mode": dataset.load_mode, "business_key": dataset.business_key}}); db.add(run); db.commit(); db.refresh(run)
    current_wm = db.scalar(select(Watermark).where(Watermark.data_source_id == source.id)); before = None
    if current_wm and current_wm.value:
        try: before = json.loads(current_wm.value)
        except json.JSONDecodeError: before = {"value": current_wm.value}
    try:
        if not _try_source_lock(db, source.id): run.status = "SKIPPED_ALREADY_RUNNING"; run.finished_at = datetime.now(timezone.utc); db.commit(); return run
        rules = _rules_snapshot(db, dataset.id); run.watermark_before = current_wm.value if current_wm else None; run.watermark_after = run.watermark_before; run.configuration_snapshot = {**run.configuration_snapshot, "validation_rules": rules}; db.commit(); db.refresh(run); options = source.config; batch_size = int(options.get("batch_size", 5000)); wm = {"column": options.get("watermark_column"), "primary_key": options.get("watermark_primary_key"), **(before or {})} if options.get("watermark_column") else None
        if dataset.load_mode == "FULL_REPLACE": db.execute(delete(DataRecord).where(DataRecord.dataset_id == dataset.id))
        last_record, _ = _process_stream(db, run, dataset, connector.extract(options["schema"], options["table"], wm, batch_size), rules, batch_size)
        column, primary_key = options.get("watermark_column"), options.get("watermark_primary_key")
        if last_record is not None and column:
            after = {"column": column, "value": _json_safe(last_record.get(column))}
            if primary_key: after.update(primary_key=primary_key, primary_key_value=_json_safe(last_record.get(primary_key)))
            if current_wm is None: current_wm = Watermark(data_source_id=source.id); db.add(current_wm)
            current_wm.value = json.dumps(after, ensure_ascii=False, separators=(",", ":")); run.watermark_after = current_wm.value
        return _finish_success(db, run, actor, {"source_type": "POSTGRESQL", "rows_read": run.rows_read, "inserted": run.rows_inserted, "updated": run.rows_updated, "watermark_after": run.watermark_after})
    except Exception as exc: return _finish_failed(db, run, exc)
