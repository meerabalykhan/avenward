"""Public health API response schemas."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    checks: dict[str, Literal["available", "unavailable"]]


class VersionResponse(BaseModel):
    name: Literal["avenward"] = "avenward"
    version: str
    environment: str
