from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from control.ranking_control import RankingControl
    from entity.recommendation_set import RecommendationSet


class ResultsListUI:
    """«boundary» Displays the ranked list of recommended subzones."""

    rankingControl: RankingControl  # private

    def __init__(self, rankingControl: RankingControl) -> None:
        """Create a ResultsListUI with its attributes (TODO: add validation if needed)."""
        self.rankingControl = rankingControl

    def renderResults(self, results: RecommendationSet) -> None:
        """Render results (public).

        Args:
            results: RecommendationSet
        """
        raise NotImplementedError  # TODO

    def onSubzoneClick(self, subzoneId: str) -> None:
        """On subzone click (public).

        Args:
            subzoneId: str
        """
        raise NotImplementedError  # TODO
