from dataclasses import dataclass
from typing import Any
from .hashing import row_hash

@dataclass
class ChangeCounts:
    inserted: int = 0; updated: int = 0; unchanged: int = 0

def apply_upsert(state: dict[str, tuple[str, dict[str, Any]]], records: list[dict[str, Any]], business_key: list[str]) -> ChangeCounts:
    """Deterministic reference implementation used by unit tests and the loader contract."""
    counts = ChangeCounts()
    for record in records:
        key = row_hash({column: record.get(column) for column in business_key}, business_key); digest = row_hash(record)
        previous = state.get(key)
        if previous is None: counts.inserted += 1
        elif previous[0] == digest: counts.unchanged += 1
        else: counts.updated += 1
        state[key] = (digest, record)
    return counts

def committed_watermark(before: str | None, after: str | None, status: str) -> str | None:
    return after if status in {"COMPLETED", "COMPLETED_WITH_WARNINGS", "COMPLETED_WITH_ERRORS"} else before
