from __future__ import annotations
from typing import Annotated, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class SourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160); description: str = ""; source_type: str = "FILE"; connection_id: UUID | None = None; config: dict[str, Any] = {}; dataset_name: str = "main"; table_name: str = "records"; load_mode: str = "INCREMENTAL_UPSERT"; business_key: list[str] = []
class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID; name: str; description: str; source_type: str; status: str; created_at: Any
class RuleCreate(BaseModel):
    column_name: str; rule_type: str; rule_config: dict[str, Any] = {}; severity: str = "ERROR"; enabled: bool = True
class ConnectionCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str = Field(min_length=1, max_length=160); engine: str = "POSTGRESQL"; host: str; port: int = 5432; database: str; schema_: Annotated[str | None, Field(alias="schema")] = None; username: str; password: str; sslmode: str = "prefer"
class ConnectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID; name: str; engine: str; config: dict[str, Any]
class ScheduleCreate(BaseModel):
    data_source_id: UUID; schedule_type: str = "MANUAL"; timezone: str = "America/Santo_Domingo"; hour: int | None = None; minute: int | None = None; interval_hours: int | None = None; day_of_week: int | None = None; day_of_month: int | None = None; cron_expression: str | None = None; enabled: bool = True; retry_count: int = 3; retry_delay_seconds: int = 300
class PreviewOut(BaseModel):
    columns: list[str]; preview: list[dict[str, Any]]; rows_estimated: int | None; inferred_types: dict[str, str]
