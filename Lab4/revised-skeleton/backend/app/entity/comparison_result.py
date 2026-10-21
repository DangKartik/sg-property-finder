from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.entity.recommendation_item import RecommendationItem
    from app.schemas.neighborhood_detail_dto import NeighborhoodDetailDTO


@dataclass
class ComparisonResult:
    profileId: str
    generatedTime: datetime
    items: list[RecommendationItem] = field(default_factory=list)
    details: list[NeighborhoodDetailDTO] = field(default_factory=list)
    bestSubzoneId: str | None = None
    summary: str = ""

    def getItems(self) -> list[RecommendationItem]: ...
    def getDetails(self) -> list[NeighborhoodDetailDTO]: ...
    def getBestSubzoneId(self) -> str | None: ...
