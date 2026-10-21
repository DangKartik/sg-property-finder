from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.entity.recommendation_item import RecommendationItem
    from app.schemas.data_availability_warning import DataAvailabilityWarning


@dataclass
class RecommendationSet:
    profileId: str
    generatedTime: datetime
    dataSnapshotId: str
    dataAsOf: datetime
    items: list[RecommendationItem] = field(default_factory=list)
    warnings: list[DataAvailabilityWarning] = field(default_factory=list)

    def addItem(self, item: RecommendationItem) -> None: ...
    def getItems(self) -> list[RecommendationItem]: ...
    def sortByRank(self) -> None: ...
