from __future__ import annotations

import calendar
import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from croniter import croniter

SCHEDULE_TYPES = {"MANUAL", "HOURLY", "EVERY_X_HOURS", "DAILY", "WEEKLY", "MONTHLY", "CRON"}
logger = logging.getLogger("kiriox.scheduler")

def next_run_at(schedule_type: str, now: datetime, timezone_name: str = "America/Santo_Domingo", *, hour: int | None = None, minute: int | None = None, interval_hours: int | None = None, day_of_week: int | None = None, day_of_month: int | None = None, cron_expression: str | None = None) -> datetime | None:
    if schedule_type == "MANUAL": return None
    local_zone = ZoneInfo(timezone_name); local_now = now.astimezone(local_zone).replace(second=0, microsecond=0)
    if schedule_type == "CRON":
        if not cron_expression: raise ValueError("CRON requiere cron_expression")
        return croniter(cron_expression, local_now).get_next(datetime).astimezone(timezone.utc)
    if schedule_type == "HOURLY": candidate = (local_now + timedelta(hours=1)).replace(minute=0)
    elif schedule_type == "EVERY_X_HOURS":
        if not interval_hours or interval_hours < 1: raise ValueError("interval_hours debe ser positivo")
        candidate = local_now + timedelta(hours=interval_hours)
    else:
        target_hour, target_minute = hour if hour is not None else 2, minute if minute is not None else 0
        candidate = local_now.replace(hour=target_hour, minute=target_minute)
        if schedule_type == "DAILY":
            if candidate <= local_now: candidate += timedelta(days=1)
        elif schedule_type == "WEEKLY":
            target_day = day_of_week if day_of_week is not None else 0; candidate += timedelta(days=(target_day - candidate.weekday()) % 7)
            if candidate <= local_now: candidate += timedelta(days=7)
        elif schedule_type == "MONTHLY":
            target_day = day_of_month if day_of_month is not None else 1; year, month = local_now.year, local_now.month
            if local_now.day >= target_day and candidate <= local_now: month += 1; year += month // 13; month = (month - 1) % 12 + 1
            candidate = candidate.replace(year=year, month=month, day=min(target_day, calendar.monthrange(year, month)[1]))
        else: raise ValueError(f"Tipo de schedule no soportado: {schedule_type}")
    return candidate.astimezone(timezone.utc)

def is_retryable_error(error: Exception) -> bool:
    text = str(error).lower()
    return any(marker in text for marker in ("timeout", "temporarily unavailable", "connection refused", "network", "could not connect"))

def retry_attempts(action, retry_count: int = 3, delay_seconds: int = 300):
    """Execute only technical failures again; callers may pass a zero delay in tests."""
    attempts = 0
    while True:
        attempts += 1
        try: return action(), attempts
        except Exception as exc:
            if attempts > retry_count or not is_retryable_error(exc): raise
            time.sleep(delay_seconds * (2 ** (attempts - 1)))

class PersistentScheduler:
    """A small DB-backed polling worker; schedules survive process restarts."""
    def __init__(self, session_factory, runner, interval_seconds: int = 15):
        self.session_factory = session_factory; self.runner = runner; self.interval_seconds = interval_seconds; self._stop = False
    def start(self) -> threading.Thread:
        thread = threading.Thread(target=self.run_forever, name="kiriox-scheduler", daemon=True); thread.start(); return thread
    def stop(self) -> None: self._stop = True
    def run_forever(self) -> None:
        while not self._stop:
            try: self.tick()
            except Exception: logger.exception("Scheduler tick failed")
            time.sleep(self.interval_seconds)
    def tick(self, now: datetime | None = None) -> int:
        from .models import Schedule
        from sqlalchemy import select, text
        current = now or datetime.now(timezone.utc); claimed = 0
        claimed_schedules = []
        with self.session_factory() as db:
            schedules = db.scalars(select(Schedule).where(Schedule.enabled.is_(True), Schedule.next_run_at <= current).with_for_update(skip_locked=True)).all()
            for schedule in schedules:
                locked = db.scalar(select(text("pg_try_advisory_xact_lock(hashtextextended(:key, 0))")).params(key=str(schedule.data_source_id)))
                if locked is False: continue
                schedule.last_run_at = current; schedule.next_run_at = next_run_at(schedule.schedule_type, current, schedule.timezone, hour=schedule.hour, minute=schedule.minute, interval_hours=schedule.interval_hours, day_of_week=schedule.day_of_week, day_of_month=schedule.day_of_month, cron_expression=schedule.cron_expression); claimed += 1; claimed_schedules.append(schedule)
            db.commit()
            for schedule in claimed_schedules:
                try:
                    retry_attempts(lambda: self.runner(schedule.data_source_id), retry_count=schedule.retry_count, delay_seconds=schedule.retry_delay_seconds)
                except Exception:
                    logger.exception("Scheduled run failed after retries", extra={"schedule_id": str(schedule.id)})
        return claimed
