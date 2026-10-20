from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from typing import BinaryIO


class PdfReport:
    """«entity» A generated PDF report of the recommendations."""

    reportId: str  # private
    contentBytes: bytes  # private
    createdAt: datetime  # private

    def __init__(self, reportId: str, contentBytes: bytes, createdAt: datetime) -> None:
        """Create a PdfReport with its attributes (TODO: add validation if needed)."""
        self.reportId = reportId
        self.contentBytes = contentBytes
        self.createdAt = createdAt

    def getFileStream(self) -> BinaryIO:
        """Get file stream (public).

        Returns:
            BinaryIO
        """
        raise NotImplementedError  # TODO
