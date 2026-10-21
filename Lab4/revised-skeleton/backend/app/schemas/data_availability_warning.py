from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.entity.types import DataAvailabilityCode, WarningSeverity


@dataclass
class DataAvailabilityWarning:
    subzoneCode: str | None
    datasetCode: str
    code: DataAvailabilityCode
    severity: WarningSeverity
    isStale: bool
    isRetryable: bool
    source: str
    message: str
    asOf: datetime | None = None
