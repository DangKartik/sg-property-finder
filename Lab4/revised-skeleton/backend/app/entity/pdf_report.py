"""Pdf report module."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PdfReport:
    """Stereotype: Entity. Entity value object containing browser-safe PDF download metadata."""
    reportId: str
    generatedTime: datetime
    downloadUrl: str
    expiresAt: datetime
    fileName: str
    contentType: str
    sizeBytes: int

    def getReportId(self) -> str:
        """Return report id.

        Args:
            None.

        Returns:
            str.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getDownloadUrl(self) -> str:
        """Return download url.

        Args:
            None.

        Returns:
            str.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getFileName(self) -> str:
        """Return file name.

        Args:
            None.

        Returns:
            str.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getExpiresAt(self) -> datetime:
        """Return expires at.

        Args:
            None.

        Returns:
            datetime.

        Failure handling:
            Not applicable at the skeleton level."""
        ...
