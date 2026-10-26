"""Dataset metadata entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class DatasetMetadata:
    """Stereotype: Entity. Dataset snapshot identity and freshness."""

    dataSnapshotId: str
    dataAsOf: datetime
    sourceUrl: str
    recordCount: int

    def getDataSnapshotId(self) -> str:
        """Return the snapshot identifier."""
        return self.dataSnapshotId

    def getDataAsOf(self) -> datetime:
        """Return the source timestamp."""
        return self.dataAsOf

    def getSourceUrl(self) -> str:
        """Return the source URL."""
        return self.sourceUrl

    def getRecordCount(self) -> int:
        """Return the record count."""
        return self.recordCount
