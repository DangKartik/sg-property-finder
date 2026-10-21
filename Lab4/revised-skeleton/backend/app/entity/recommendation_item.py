from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.entity.criterion_score import CriterionScore


@dataclass
class RecommendationItem:
    subzoneId: str
    subzoneName: str
    rank: int
    totalScore: float
    criterionScores: list[CriterionScore] = field(default_factory=list)

    def getSubzoneId(self) -> str: ...
    def getRank(self) -> int: ...
    def getTotalScore(self) -> float: ...
    def getCriterionScores(self) -> list[CriterionScore]: ...
