"""Dataset metadata module."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DatasetMetadata:
    """Stereotype: Entity. Entity value object identifying a dataset snapshot, its source and freshness."""
    dataSnapshotId: str
    dataAsOf: datetime
    sourceUrl: str
    recordCount: int

    def getDataSnapshotId(self) -> str:
        """Return data snapshot id.

        Args:
            None.

        Returns:
            str.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getDataAsOf(self) -> datetime:
        """Return data as of.

        Args:
            None.

        Returns:
            datetime.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getSourceUrl(self) -> str:
        """Return source url.

        Args:
            None.

        Returns:
            str.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getRecordCount(self) -> int:
        """Return record count.

        Args:
            None.

        Returns:
            int.

        Failure handling:
            Not applicable at the skeleton level."""
        ...
