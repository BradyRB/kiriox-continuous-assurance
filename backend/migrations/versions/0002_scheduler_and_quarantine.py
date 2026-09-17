"""Add scheduler persistence and dataset identity to quarantine."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_scheduler_and_quarantine"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    op.add_column("quarantine_records", sa.Column("dataset_id", uuid, sa.ForeignKey("ingestion.datasets.id"), nullable=True), schema="raw")
    op.create_table("schedules", sa.Column("id", uuid, primary_key=True), sa.Column("data_source_id", uuid, sa.ForeignKey("ingestion.data_sources.id"), nullable=False), sa.Column("schedule_type", sa.String(30), nullable=False, server_default="MANUAL"), sa.Column("timezone", sa.String(64), nullable=False, server_default="America/Santo_Domingo"), sa.Column("hour", sa.Integer()), sa.Column("minute", sa.Integer()), sa.Column("interval_hours", sa.Integer()), sa.Column("day_of_week", sa.Integer()), sa.Column("day_of_month", sa.Integer()), sa.Column("cron_expression", sa.String(120)), sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("retry_count", sa.Integer(), nullable=False, server_default="3"), sa.Column("retry_delay_seconds", sa.Integer(), nullable=False, server_default="300"), sa.Column("next_run_at", sa.DateTime(timezone=True)), sa.Column("last_run_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), schema="ingestion")

def downgrade() -> None:
    op.drop_table("schedules", schema="ingestion")
    op.drop_column("quarantine_records", "dataset_id", schema="raw")
