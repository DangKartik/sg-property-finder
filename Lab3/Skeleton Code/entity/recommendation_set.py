from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from sgpropfinder.entity.recommendation_item import RecommendationItem


class RecommendationSet:
    """«entity»"""

    profileId: str
    generatedTime: datetime
    items: list[RecommendationItem]

    def addItem(self, item: RecommendationItem) -> None:
        raise NotImplementedError  # TODO

    def getItems(self) -> list[RecommendationItem]:
        raise NotImplementedError  # TODO

    def sortByRank(self) -> None:
        raise NotImplementedError  # TODO
