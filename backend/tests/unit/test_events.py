from datetime import UTC

import pytest

from app.events import normalize_record, records_from_upload


def test_json_csv_and_jsonl_are_parsed_as_data() -> None:
    assert records_from_upload("events.json", b'{"title":"one"}') == [{"title": "one"}]
    assert records_from_upload("events.jsonl", b'{"title":"one"}\n{"title":"two"}') == [
        {"title": "one"},
        {"title": "two"},
    ]
    assert records_from_upload("events.csv", b"title,severity\none,low\n") == [
        {"title": "one", "severity": "low"}
    ]


def test_unsupported_invalid_and_non_utf8_files_fail_closed() -> None:
    with pytest.raises(ValueError, match="Only"):
        records_from_upload("events.exe", b"ignored")
    with pytest.raises(ValueError, match="not valid"):
        records_from_upload("events.json", b"{")
    with pytest.raises(ValueError, match="UTF-8"):
        records_from_upload("events.json", b"\xff")


def test_normalization_requires_supported_severity_and_timezone() -> None:
    event = normalize_record(
        {
            "source": "identity",
            "category": "authentication",
            "severity": "HIGH",
            "title": "Synthetic sign-in",
            "observed_at": "2026-07-23T10:00:00+05:00",
        }
    )
    assert event.severity == "high"
    assert event.observed_at.tzinfo == UTC
    assert event.raw["source"] == "identity"
    with pytest.raises(ValueError, match="severity"):
        normalize_record({"severity": "dramatic", "observed_at": "2026-07-23T10:00:00Z"})
    with pytest.raises(ValueError, match="timezone"):
        normalize_record({"severity": "low", "observed_at": "2026-07-23T10:00:00"})
    with pytest.raises(ValueError, match="object"):
        normalize_record([])  # type: ignore[arg-type]
