import uuid
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Connection(Base):
    __tablename__ = "connections"; __table_args__ = {"schema": "ingestion"}
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160)); engine: Mapped[str] = mapped_column(String(30))
    config: Mapped[dict] = mapped_column(JSONB, default=dict); secret_ciphertext: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class DataSource(Base):
    __tablename__ = "data_sources"; __table_args__ = {"schema": "ingestion"}
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160), unique=True); description: Mapped[str] = mapped_column(Text, default="")
    source_type: Mapped[str] = mapped_column(String(30)); connection_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ingestion.connections.id"))
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE"); config: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_by: Mapped[str] = mapped_column(String(160), default="local-user"); created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now()); updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Dataset(Base):
    __tablename__ = "datasets"; __table_args__ = (UniqueConstraint("data_source_id", "name"), {"schema": "ingestion"})
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4); data_source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ingestion.data_sources.id"))
    name: Mapped[str] = mapped_column(String(160)); schema_name: Mapped[str] = mapped_column(String(63), default="data"); table_name: Mapped[str] = mapped_column(String(160), default="records")
    load_mode: Mapped[str] = mapped_column(String(30), default="INCREMENTAL_UPSERT"); business_key: Mapped[list] = mapped_column(JSON, default=list); missing_record_behavior: Mapped[str] = mapped_column(String(30), default="IGNORE"); columns: Mapped[dict] = mapped_column(JSONB, default=dict)

class ValidationRule(Base):
    __tablename__ = "validation_rules"; __table_args__ = {"schema": "ingestion"}
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4); dataset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ingestion.datasets.id")); column_name: Mapped[str] = mapped_column(String(160)); rule_type: Mapped[str] = mapped_column(String(40)); rule_config: Mapped[dict] = mapped_column(JSONB, default=dict); severity: Mapped[str] = mapped_column(String(20), default="ERROR"); enabled: Mapped[bool] = mapped_column(Boolean, default=True)

class FileVersion(Base):
    __tablename__ = "file_versions"; __table_args__ = (UniqueConstraint("data_source_id", "sha256"), {"schema": "ingestion"})
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4); data_source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ingestion.data_sources.id")); filename: Mapped[str] = mapped_column(String(260)); file_size: Mapped[int] = mapped_column(BigInteger); sha256: Mapped[str] = mapped_column(String(64)); uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now()); uploaded_by: Mapped[str] = mapped_column(String(160)); processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True)); status: Mapped[str] = mapped_column(String(30), default="RECEIVED")

class LoadRun(Base):
    __tablename__ = "load_runs"; __table_args__ = {"schema": "ingestion"}
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4); data_source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ingestion.data_sources.id")); file_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ingestion.file_versions.id")); started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now()); finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True)); status: Mapped[str] = mapped_column(String(40), default="RUNNING"); rows_read: Mapped[int] = mapped_column(BigInteger, default=0); rows_inserted: Mapped[int] = mapped_column(BigInteger, default=0); rows_updated: Mapped[int] = mapped_column(BigInteger, default=0); rows_unchanged: Mapped[int] = mapped_column(BigInteger, default=0); rows_rejected: Mapped[int] = mapped_column(BigInteger, default=0); error_count: Mapped[int] = mapped_column(BigInteger, default=0); warning_count: Mapped[int] = mapped_column(BigInteger, default=0); watermark_before: Mapped[str | None] = mapped_column(String(160)); watermark_after: Mapped[str | None] = mapped_column(String(160)); configuration_snapshot: Mapped[dict] = mapped_column(JSONB, default=dict)

class LoadRunError(Base):
    __tablename__ = "load_run_errors"; __table_args__ = {"schema": "ingestion"}
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4); run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ingestion.load_runs.id")); error_type: Mapped[str] = mapped_column(String(30)); message: Mapped[str] = mapped_column(Text); created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class QuarantineRecord(Base):
    __tablename__ = "quarantine_records"; __table_args__ = {"schema": "raw"}
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4); run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ingestion.load_runs.id")); dataset_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ingestion.datasets.id")); dataset: Mapped[str] = mapped_column(String(160)); row_number: Mapped[int] = mapped_column(BigInteger); business_key: Mapped[dict | None] = mapped_column(JSONB); raw_record: Mapped[dict] = mapped_column(JSONB); column_name: Mapped[str | None] = mapped_column(String(160)); value: Mapped[str | None] = mapped_column(Text); rule: Mapped[str] = mapped_column(String(40)); error_code: Mapped[str] = mapped_column(String(60)); error_message: Mapped[str] = mapped_column(Text); created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class RawRecord(Base):
    __tablename__ = "raw_records"; __table_args__ = {"schema": "raw"}
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4); run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ingestion.load_runs.id")); row_number: Mapped[int] = mapped_column(BigInteger); record: Mapped[dict] = mapped_column(JSONB); row_hash: Mapped[str] = mapped_column(String(64))

class DataRecord(Base):
    __tablename__ = "data_records"; __table_args__ = (UniqueConstraint("dataset_id", "business_key_hash"), {"schema": "data"})
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4); dataset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ingestion.datasets.id")); run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ingestion.load_runs.id")); business_key_hash: Mapped[str] = mapped_column(String(64)); row_hash: Mapped[str] = mapped_column(String(64)); record: Mapped[dict] = mapped_column(JSONB); is_active: Mapped[bool] = mapped_column(Boolean, default=True); updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class AuditEvent(Base):
    __tablename__ = "audit_events"; __table_args__ = {"schema": "audit"}
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4); event_type: Mapped[str] = mapped_column(String(80)); actor: Mapped[str] = mapped_column(String(160)); object_type: Mapped[str] = mapped_column(String(80)); object_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True)); payload: Mapped[dict] = mapped_column(JSONB, default=dict); created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Watermark(Base):
    __tablename__ = "watermarks"; __table_args__ = {"schema": "ingestion"}
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4); data_source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ingestion.data_sources.id"), unique=True); value: Mapped[str | None] = mapped_column(String(160)); updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Schedule(Base):
    __tablename__ = "schedules"; __table_args__ = {"schema": "ingestion"}
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4); data_source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ingestion.data_sources.id")); schedule_type: Mapped[str] = mapped_column(String(30), default="MANUAL"); timezone: Mapped[str] = mapped_column(String(64), default="America/Santo_Domingo"); hour: Mapped[int | None] = mapped_column(); minute: Mapped[int | None] = mapped_column(); interval_hours: Mapped[int | None] = mapped_column(); day_of_week: Mapped[int | None] = mapped_column(); day_of_month: Mapped[int | None] = mapped_column(); cron_expression: Mapped[str | None] = mapped_column(String(120)); enabled: Mapped[bool] = mapped_column(Boolean, default=True); retry_count: Mapped[int] = mapped_column(default=3); retry_delay_seconds: Mapped[int] = mapped_column(default=300); next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True)); last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True)); created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now()); updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
