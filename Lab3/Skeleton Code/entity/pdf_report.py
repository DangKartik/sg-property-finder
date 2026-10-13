from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


class PdfReport:
    """«entity»"""

    reportId: str
    generatedTime: datetime
    filePath: str

    def getReportId(self) -> str:
        raise NotImplementedError  # TODO

    def getFilePath(self) -> str:
        raise NotImplementedError  # TODO
