"""Recommendation item entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.entity.criterion_score import CriterionScore


@dataclass
class RecommendationItem:
    """Stereotype: Entity. One ranked subzone with its score breakdown."""

    subzoneId: str
    subzoneName: str
    rank: int
    totalScore: float
    criterionScores: list[CriterionScore] = field(default_factory=list)

    def getSubzoneId(self) -> str:
        """Return the subzone code."""
        return self.subzoneId

    def getRank(self) -> int:
        """Return the 1-based rank."""
        return self.rank

    def getTotalScore(self) -> float:
        """Return the 0-100 score."""
        return self.totalScore

    def getCriterionScores(self) -> list[CriterionScore]:
        """Return the per-criterion score rows."""
        return list(self.criterionScores)
