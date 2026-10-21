"""Comparison result module."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.entity.recommendation_item import RecommendationItem
    from app.schemas.neighborhood_detail_dto import NeighborhoodDetailDTO

@dataclass
class ComparisonResult:
    """Stereotype: Entity. Entity representing side-by-side comparison data for selected subzones."""
    profileId: str
    generatedTime: datetime
    items: list[RecommendationItem] = field(default_factory=list)
    details: list[NeighborhoodDetailDTO] = field(default_factory=list)
    bestSubzoneId: str | None = None
    summary: str = ''

    def getItems(self) -> list[RecommendationItem]:
        """Return items.

        Args:
            None.

        Returns:
            list[RecommendationItem].

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getDetails(self) -> list[NeighborhoodDetailDTO]:
        """Return details.

        Args:
            None.

        Returns:
            list[NeighborhoodDetailDTO].

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getBestSubzoneId(self) -> str | None:
        """Return best subzone id.

        Args:
            None.

        Returns:
            str | None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...
