from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entity.pdf_report import PdfReport
    from entity.recommendation_set import RecommendationSet


class ReportControl:
    """«control» Generates the PDF report and exports it to a file."""

    lastGeneratedReport: PdfReport  # private

    def __init__(self, lastGeneratedReport: PdfReport) -> None:
        """Create a ReportControl with its attributes (TODO: add validation if needed)."""
        self.lastGeneratedReport = lastGeneratedReport

    def generatePdfReport(self, recommendationSet: RecommendationSet) -> PdfReport:
        """Generate pdf report (public).

        Args:
            recommendationSet: RecommendationSet
        Returns:
            PdfReport
        """
        raise NotImplementedError  # TODO

    def exportToFile(self, report: PdfReport, filePath: str) -> bool:
        """Export to file (public).

        Args:
            report: PdfReport
            filePath: str
        Returns:
            bool
        """
        raise NotImplementedError  # TODO
