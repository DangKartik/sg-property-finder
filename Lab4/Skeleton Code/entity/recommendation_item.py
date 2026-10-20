from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class RecommendationItem:
    """«entity»"""

    subzoneId: str
    rank: int
    totalScore: float
    criterionScoreBreakdown: dict[str, float]

    def getSubzoneId(self) -> str:
        raise NotImplementedError  # TODO

    def getRank(self) -> int:
        raise NotImplementedError  # TODO

    def getTotalScore(self) -> float:
        raise NotImplementedError  # TODO
