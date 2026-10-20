from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entity.subzone import Subzone


class RecommendationItem:
    """«entity» One ranked subzone with its suitability score."""

    rank: int  # private
    totalScore: float  # private
    targetSubzone: Subzone  # private

    def __init__(self, rank: int, totalScore: float, targetSubzone: Subzone) -> None:
        """Create a RecommendationItem with its attributes (TODO: add validation if needed)."""
        self.rank = rank
        self.totalScore = totalScore
        self.targetSubzone = targetSubzone

    def getRank(self) -> int:
        """Get rank (public).

        Returns:
            int
        """
        raise NotImplementedError  # TODO

    def getScore(self) -> float:
        """Get score (public).

        Returns:
            float
        """
        raise NotImplementedError  # TODO

    def getSubzone(self) -> Subzone:
        """Get subzone (public).

        Returns:
            Subzone
        """
        raise NotImplementedError  # TODO
