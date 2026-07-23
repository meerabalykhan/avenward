"""Safe parsing and canonical normalization for supported event files."""

import csv
import io
import json
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator


class NormalizedEvent(BaseModel):
    source: str = Field(min_length=1, max_length=80)
    category: str = Field(min_length=1, max_length=80)
    severity: str
    title: str = Field(min_length=1, max_length=240)
    actor: str | None = Field(default=None, max_length=240)
    target: str | None = Field(default=None, max_length=240)
    observed_at: datetime
    confidence: int = Field(default=100, ge=0, le=100)
    summary: str = Field(default="No additional context supplied.", max_length=2000)
    raw: dict[str, Any]

    @field_validator("severity")
    @classmethod
    def valid_severity(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"informational", "low", "medium", "high", "critical"}:
            raise ValueError("unsupported severity")
        return normalized

    @field_validator("observed_at")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("observed_at must include a timezone")
        return value.astimezone(UTC)


def records_from_upload(filename: str, content: bytes) -> list[dict[str, Any]]:
    """Decode supported data files without evaluating their contents."""

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("File must use UTF-8 encoding") from exc
    suffix = filename.lower().rsplit(".", 1)[-1]
    try:
        if suffix == "csv":
            return [dict(row) for row in csv.DictReader(io.StringIO(text))]
        if suffix == "jsonl":
            return [json.loads(line) for line in text.splitlines() if line.strip()]
        if suffix == "json":
            decoded = json.loads(text)
            return decoded if isinstance(decoded, list) else [decoded]
    except (csv.Error, json.JSONDecodeError) as exc:
        raise ValueError("File content is not valid for its format") from exc
    raise ValueError("Only .csv, .json, and .jsonl files are supported")


def normalize_record(record: dict[str, Any]) -> NormalizedEvent:
    """Map the documented generic schema to a canonical event."""

    if not isinstance(record, dict):
        raise ValueError("Every event must be an object")
    try:
        return NormalizedEvent(
            source=record.get("source", "generic"),
            category=record.get("category", "activity"),
            severity=record.get("severity", "informational"),
            title=record.get("title", "Imported event"),
            actor=record.get("actor") or None,
            target=record.get("target") or None,
            observed_at=record.get("observed_at"),
            confidence=record.get("confidence", 100),
            summary=record.get("summary", "No additional context supplied."),
            raw=record,
        )
    except ValidationError as exc:
        raise ValueError(exc.errors(include_url=False)[0]["msg"]) from exc
