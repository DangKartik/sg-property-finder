from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class DatasetMetadata:
    dataSnapshotId: str
    dataAsOf: datetime
    sourceUrl: str
    recordCount: int

    def getDataSnapshotId(self) -> str: ...
    def getDataAsOf(self) -> datetime: ...
    def getSourceUrl(self) -> str: ...
    def getRecordCount(self) -> int: ...
