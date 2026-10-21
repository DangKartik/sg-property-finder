"""Recommendation item module."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.entity.criterion_score import CriterionScore

@dataclass
class RecommendationItem:
    """Stereotype: Entity. Entity representing one ranked subzone and its criterion-level score breakdown."""
    subzoneId: str
    subzoneName: str
    rank: int
    totalScore: float
    criterionScores: list[CriterionScore] = field(default_factory=list)

    def getSubzoneId(self) -> str:
        """Return subzone id.

        Args:
            None.

        Returns:
            str.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getRank(self) -> int:
        """Return rank.

        Args:
            None.

        Returns:
            int.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getTotalScore(self) -> float:
        """Return total score.

        Args:
            None.

        Returns:
            float.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getCriterionScores(self) -> list[CriterionScore]:
        """Return criterion scores.

        Args:
            None.

        Returns:
            list[CriterionScore].

        Failure handling:
            Not applicable at the skeleton level."""
        ...
