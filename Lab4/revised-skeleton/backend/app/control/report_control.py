from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.control.data_availability_notifier import DataAvailabilityNotifier
    from app.entity.pdf_report import PdfReport
    from app.entity.recommendation_set import RecommendationSet
    from app.schemas.neighborhood_detail_dto import NeighborhoodDetailDTO


class ReportControl:
    notifier: DataAvailabilityNotifier

    def __init__(self, notifier: DataAvailabilityNotifier) -> None: ...
    def generatePdfReport(
        self,
        recommendations: RecommendationSet,
        details: list[NeighborhoodDetailDTO],
    ) -> PdfReport: ...
    def exportToFile(self, report: PdfReport, filePath: str) -> bool: ...
