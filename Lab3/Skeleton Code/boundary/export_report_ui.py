from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from control.report_control import ReportControl


class ExportReportUI:
    """«boundary» Export dialog used to download the recommendations as a PDF report."""

    reportControl: ReportControl  # private

    def __init__(self, reportControl: ReportControl) -> None:
        """Create a ExportReportUI with its attributes (TODO: add validation if needed)."""
        self.reportControl = reportControl

    def openExportModal(self) -> None:
        """Open export modal (public)."""
        raise NotImplementedError  # TODO

    def onConfirmExport(self, format: str) -> None:
        """On confirm export (public).

        Args:
            format: str
        """
        raise NotImplementedError  # TODO
