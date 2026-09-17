from __future__ import annotations
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any
from dateutil.parser import isoparse

@dataclass(frozen=True)
class ValidationIssue:
    column: str; rule: str; severity: str; code: str; message: str; value: str | None

def _number(value: Any) -> Decimal:
    return Decimal(str(value).strip())

def validate_row(record: dict[str, Any], rules: list[dict[str, Any]], seen: dict[str, set[str]] | None = None) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for rule in rules:
        if not rule.get("enabled", True): continue
        column = rule["column_name"]; value = record.get(column); text = None if value is None else str(value)
        kind = rule["rule_type"].upper(); cfg = rule.get("rule_config") or {}; severity = rule.get("severity", "ERROR").upper()
        def add(code: str, message: str): issues.append(ValidationIssue(column, kind, severity, code, message, text))
        if kind == "REQUIRED" and (value is None or str(value).strip() == ""): add("REQUIRED", f"{column} es obligatorio")
        elif value not in (None, ""):
            try:
                if kind in ("NUMERIC", "DECIMAL"): _number(value)
                elif kind == "INTEGER" and int(str(value).strip()) != Decimal(str(value).strip()): add("INVALID_INTEGER", f"{column} debe ser entero")
                elif kind == "DATE": isoparse(str(value).strip())
                elif kind == "MAX_LENGTH" and len(str(value)) > int(cfg.get("max", cfg.get("value", 0))): add("MAX_LENGTH", f"{column} supera la longitud máxima")
                elif kind == "ALLOWED_VALUES" and value not in cfg.get("values", []): add("NOT_ALLOWED", f"{column} no está permitido")
                elif kind in ("MIN", "MAX", "RANGE"):
                    number = _number(value); low = cfg.get("min"); high = cfg.get("max")
                    if kind == "MIN" and number < _number(cfg.get("value")): add("BELOW_MIN", f"{column} es menor al mínimo")
                    if kind == "MAX" and number > _number(cfg.get("value")): add("ABOVE_MAX", f"{column} supera el máximo")
                    if kind == "RANGE" and ((low is not None and number < _number(low)) or (high is not None and number > _number(high))): add("OUT_OF_RANGE", f"{column} está fuera de rango")
                elif kind == "REGEX" and re.fullmatch(str(cfg.get("pattern", "")), str(value)) is None: add("REGEX_MISMATCH", f"{column} no coincide con el patrón")
            except (ValueError, TypeError, InvalidOperation, OverflowError):
                add({"DATE": "INVALID_DATE", "INTEGER": "INVALID_INTEGER"}.get(kind, "INVALID_NUMBER"), f"{column} tiene un valor inválido")
        if kind == "UNIQUE" and seen is not None:
            bucket = seen.setdefault(column, set()); marker = str(value)
            if marker in bucket: add("DUPLICATE", f"{column} debe ser único")
            bucket.add(marker)
    return issues

def infer_types(records: list[dict[str, Any]]) -> dict[str, str]:
    if not records: return {}
    result: dict[str, str] = {}
    for column in records[0]:
        values = [row.get(column) for row in records if row.get(column) not in (None, "")]
        if values and all(re.fullmatch(r"[-+]?\d+", str(v)) for v in values): result[column] = "INTEGER"
        elif values:
            try: [Decimal(str(v)) for v in values]; result[column] = "DECIMAL"
            except InvalidOperation:
                try: [isoparse(str(v)) for v in values]; result[column] = "DATE"
                except (ValueError, TypeError): result[column] = "TEXT"
        else: result[column] = "TEXT"
    return result
