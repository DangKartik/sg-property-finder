"""Recommendation set entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.entity.data_availability_warning import DataAvailabilityWarning
    from app.entity.recommendation_item import RecommendationItem


@dataclass
class RecommendationSet:
    """Stereotype: Entity. Ordered recommendations for one profile snapshot."""

    profileId: str
    generatedTime: datetime
    dataSnapshotId: str
    dataAsOf: datetime
    items: list[RecommendationItem] = field(default_factory=list)
    warnings: list[DataAvailabilityWarning] = field(default_factory=list)
    profileSnapshot: dict[str, Any] | None = None

    def addItem(self, item: RecommendationItem) -> None:
        """Append a recommendation item."""
        self.items.append(item)

    def getItems(self) -> list[RecommendationItem]:
        """Return the recommendation items in rank order."""
        return list(self.items)

    def sortByRank(self) -> None:
        """Sort items ascending by rank."""
        self.items.sort(key=lambda item: item.getRank())
