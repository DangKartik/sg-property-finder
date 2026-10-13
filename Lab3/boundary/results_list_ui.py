from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.entity.recommendation_item import RecommendationItem
    from sgpropfinder.entity.recommendation_set import RecommendationSet


class ResultsListUI:
    """«boundary»"""

    displayedRecommendations: list[RecommendationItem]

    def renderResults(self, recommendationSet: RecommendationSet) -> None:
        raise NotImplementedError  # TODO

    def onSubzoneClick(self, subzoneId: str) -> None:
        raise NotImplementedError  # TODO
