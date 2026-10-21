from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.entity.commute_estimate import CommuteEstimate
    from app.entity.criterion_score import CriterionScore
    from app.entity.preference_profile import PreferenceProfile
    from app.entity.subzone import Subzone


class ScoringStrategy(ABC):
    @abstractmethod
    def computeSuitabilityScore(
        self,
        subzone: Subzone,
        profile: PreferenceProfile,
        commute: CommuteEstimate,
    ) -> float: ...
    @abstractmethod
    def computeCriterionScores(
        self,
        subzone: Subzone,
        profile: PreferenceProfile,
        commute: CommuteEstimate,
    ) -> list[CriterionScore]: ...
