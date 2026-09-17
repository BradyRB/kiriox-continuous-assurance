from datetime import datetime, timezone
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient

from app.connectors import SQLAlchemyConnector, safe_identifier
from app.main import app, preview_upload
from app.pipeline import _json_safe
from app.scheduler import is_retryable_error, next_run_at, retry_attempts
from app.security import SecretBox

def test_credentials_are_authenticated_and_reversible():
    box = SecretBox("local-test-master-key")
    encrypted = box.encrypt("secret-value")
    assert encrypted != "secret-value" and box.decrypt(encrypted) == "secret-value"
    with pytest.raises(Exception): SecretBox("other-key").decrypt(encrypted)

def test_identifier_rejects_null_bytes():
    with pytest.raises(ValueError): safe_identifier("transactions\x00; DROP TABLE users")

def test_retry_classification():
    assert is_retryable_error(RuntimeError("connection timeout"))
    assert not is_retryable_error(ValueError("INVALID_NUMBER"))

def test_retries_transient_failures_only():
    calls = []
    def flaky():
        calls.append(1)
        if len(calls) < 3: raise RuntimeError("connection timeout")
        return "ok"
    assert retry_attempts(flaky, retry_count=3, delay_seconds=0) == ("ok", 3)

def test_scheduler_is_timezone_aware_and_persistent_ready():
    now = datetime(2026, 9, 14, 15, 30, tzinfo=timezone.utc)
    result = next_run_at("DAILY", now, "America/Santo_Domingo", hour=2, minute=0)
    assert result is not None and result.tzinfo is not None and result > now

def test_cron_scheduler_calculation():
    result = next_run_at("CRON", datetime(2026, 9, 14, 15, 30, tzinfo=timezone.utc), "America/Santo_Domingo", cron_expression="*/15 * * * *")
    assert result is not None and result.tzinfo is not None

def test_preview_upload_does_not_require_a_persisted_source():
    upload = UploadFile(filename="transactions.csv", file=BytesIO(b"ID,Amount\n1,100\n2,200\n"))
    result = preview_upload(upload, '{"preview_rows": 1}')
    assert result.columns == ["ID", "Amount"] and len(result.preview) == 1

def test_preview_http_accepts_reader_options_from_multipart_form():
    client = TestClient(app)
    response = client.post(
        "/api/preview",
        files={"file": ("transactions.xml", b"<transactions><transaction><ID>1</ID></transaction></transactions>", "application/xml")},
        data={"reader_options": '{"record_tag":"transaction"}'},
    )
    assert response.status_code == 200 and response.json()["columns"] == ["ID"]

def test_supported_sqlalchemy_connector_url_mapping():
    connector = SQLAlchemyConnector({"engine": "MYSQL", "host": "db", "port": 3306, "database": "demo", "username": "reader"}, "secret")
    assert connector._url().drivername == "mysql+pymysql" and connector._url().database == "demo"

def test_json_safe_normalizes_uuid_for_jsonb_records():
    value = uuid4()
    assert _json_safe({"id": value}) == {"id": str(value)}
