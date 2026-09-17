from pathlib import Path
from app.change_detection import apply_upsert, committed_watermark
from app.hashing import file_sha256, row_hash
from app.readers import DelimitedReader
from app.validation import validate_row

def test_upsert_fundamental_case():
    state = {}; first = [{"ID":"1","Amount":"100"},{"ID":"2","Amount":"200"},{"ID":"3","Amount":"300"}]
    second = [{"ID":"1","Amount":"100"},{"ID":"2","Amount":"250"},{"ID":"3","Amount":"300"},{"ID":"4","Amount":"400"}]
    apply_upsert(state, first, ["ID"]); counts = apply_upsert(state, second, ["ID"])
    assert (counts.inserted, counts.updated, counts.unchanged) == (1, 1, 2)
    assert state[row_hash({"ID":"2"}, ["ID"])][1]["Amount"] == "250"

def test_file_unchanged(tmp_path: Path):
    path = tmp_path / "same.csv"; path.write_text("ID,Amount\n1,100\n", encoding="utf-8")
    assert file_sha256(path) == file_sha256(path)

def test_data_validation_quarantines_invalid_number():
    issues = validate_row({"ID":"2", "Amount":"ABC"}, [{"column_name":"Amount","rule_type":"NUMERIC","severity":"ERROR","rule_config":{}}])
    assert len(issues) == 1 and issues[0].code == "INVALID_NUMBER"

def test_watermark_advances_only_after_commit():
    assert committed_watermark("2026-09-12T08:00:00Z", "2026-09-12T09:00:00Z", "FAILED") == "2026-09-12T08:00:00Z"
    assert committed_watermark("2026-09-12T08:00:00Z", "2026-09-12T09:00:00Z", "COMPLETED") == "2026-09-12T09:00:00Z"

def test_csv_preview_is_bounded(tmp_path: Path):
    path = tmp_path / "data.csv"; path.write_text("ID,Amount\n1,100\n2,200\n", encoding="utf-8")
    profile = DelimitedReader().profile(path, {"preview_rows": 1})
    assert len(profile.preview) == 1 and profile.columns == ["ID", "Amount"]
