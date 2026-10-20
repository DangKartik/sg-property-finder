from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.control.data_availability_notifier import DataAvailabilityNotifier
    from sgpropfinder.entity.types import NeighborhoodDetailDTO
    from sgpropfinder.entity.pdf_report import PdfReport
    from sgpropfinder.entity.recommendation_set import RecommendationSet


class ReportControl:
    """«control»"""

    notifier: DataAvailabilityNotifier

    def generatePdfReport(self, recommendations: RecommendationSet, details: list[NeighborhoodDetailDTO]) -> PdfReport:
        raise NotImplementedError  # TODO
