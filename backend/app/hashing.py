from __future__ import annotations
import hashlib
import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

def canonical_value(value: Any) -> Any:
    if value is None: return None
    if isinstance(value, Decimal): return format(value, "f")
    if isinstance(value, (datetime, date)): return value.isoformat()
    if isinstance(value, float): return format(value, ".15g")
    if isinstance(value, str): return value.strip()
    if isinstance(value, (dict, list)): return value
    return str(value)

def canonical_json(record: dict[str, Any], columns: list[str] | None = None) -> str:
    keys = columns or sorted(record)
    payload = [(key, canonical_value(record.get(key))) for key in keys]
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=False)

def row_hash(record: dict[str, Any], columns: list[str] | None = None) -> str:
    return hashlib.sha256(canonical_json(record, columns).encode("utf-8")).hexdigest()

def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()
