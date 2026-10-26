"""PDF report entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PdfReport:
    """Stereotype: Entity. Browser-safe PDF download metadata."""

    reportId: str
    generatedTime: datetime
    downloadUrl: str
    expiresAt: datetime
    fileName: str
    contentType: str
    sizeBytes: int

    def getReportId(self) -> str:
        """Return the report identifier."""
        return self.reportId

    def getDownloadUrl(self) -> str:
        """Return the short-lived download URL."""
        return self.downloadUrl

    def getFileName(self) -> str:
        """Return the download filename."""
        return self.fileName

    def getExpiresAt(self) -> datetime:
        """Return the URL expiry timestamp."""
        return self.expiresAt
