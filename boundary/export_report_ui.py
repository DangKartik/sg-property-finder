from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class ExportReportUI:
    """«boundary»"""

    reportFormat: str

    def renderExportModal(self) -> None:
        raise NotImplementedError  # TODO

    def triggerPdfExport(self) -> None:
        raise NotImplementedError  # TODO

    def displayDownloadLink(self, filePath: str) -> None:
        raise NotImplementedError  # TODO
