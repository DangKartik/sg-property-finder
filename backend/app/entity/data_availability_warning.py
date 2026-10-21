"""Data availability warning module."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from app.entity.enums import DataAvailabilityCode, WarningSeverity

@dataclass
class DataAvailabilityWarning:
    """Stereotype: Entity. Entity value object describing missing, stale, partial or valid-zero data."""
    subzoneCode: str | None
    datasetCode: str
    code: DataAvailabilityCode
    severity: WarningSeverity
    isStale: bool
    isRetryable: bool
    source: str
    message: str
    asOf: datetime | None = None
