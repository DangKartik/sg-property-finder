from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PdfReport:
    reportId: str
    generatedTime: datetime
    downloadUrl: str
    expiresAt: datetime
    fileName: str
    contentType: str
    sizeBytes: int

    def getReportId(self) -> str: ...
    def getDownloadUrl(self) -> str: ...
    def getFileName(self) -> str: ...
    def getExpiresAt(self) -> datetime: ...
