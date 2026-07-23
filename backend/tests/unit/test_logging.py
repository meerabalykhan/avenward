import json
import logging

from app.core.logging import JsonFormatter


def test_json_formatter_emits_expected_fields() -> None:
    record = logging.LogRecord("avenward", logging.INFO, __file__, 1, "started", (), None)
    record.request_id = "request-1"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "avenward"
    assert payload["message"] == "started"
    assert payload["request_id"] == "request-1"
    assert "timestamp" in payload
