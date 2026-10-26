"""Comparison result entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.entity.recommendation_item import RecommendationItem
    from app.schemas.neighborhood_detail_dto import NeighborhoodDetailDTO


@dataclass
class ComparisonResult:
    """Stereotype: Entity. Side-by-side comparison items and factsheets."""

    profileId: str
    generatedTime: datetime
    items: list[RecommendationItem] = field(default_factory=list)
    details: list[NeighborhoodDetailDTO] = field(default_factory=list)
    bestSubzoneId: str | None = None
    summary: str = ""

    def getItems(self) -> list[RecommendationItem]:
        """Return comparison score items."""
        return list(self.items)

    def getDetails(self) -> list[NeighborhoodDetailDTO]:
        """Return full factsheets for the compared subzones."""
        return list(self.details)

    def getBestSubzoneId(self) -> str | None:
        """Return the highest-scoring subzone code."""
        return self.bestSubzoneId
