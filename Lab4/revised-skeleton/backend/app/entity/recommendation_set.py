"""Recommendation set module."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.entity.data_availability_warning import DataAvailabilityWarning
    from app.entity.recommendation_item import RecommendationItem

@dataclass
class RecommendationSet:
    """Stereotype: Entity. Entity representing an ordered set of recommendations for one profile snapshot."""
    profileId: str
    generatedTime: datetime
    dataSnapshotId: str
    dataAsOf: datetime
    items: list[RecommendationItem] = field(default_factory=list)
    warnings: list[DataAvailabilityWarning] = field(default_factory=list)

    def addItem(self, item: RecommendationItem) -> None:
        """Add item.

        Args:
            item: RecommendationItem

        Returns:
            None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getItems(self) -> list[RecommendationItem]:
        """Return items.

        Args:
            None.

        Returns:
            list[RecommendationItem].

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def sortByRank(self) -> None:
        """Sort by rank in place.

        Args:
            None.

        Returns:
            None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...
