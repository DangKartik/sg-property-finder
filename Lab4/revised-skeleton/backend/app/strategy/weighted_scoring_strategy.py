from __future__ import annotations

from typing import TYPE_CHECKING

from app.strategy.scoring_strategy import ScoringStrategy

if TYPE_CHECKING:
    from app.entity.commute_estimate import CommuteEstimate
    from app.entity.criterion_score import CriterionScore
    from app.entity.preference_profile import PreferenceProfile
    from app.entity.subzone import Subzone
    from app.strategy.criterion_catalog import CriterionCatalog


class WeightedScoringStrategy(ScoringStrategy):
    criterionCatalog: CriterionCatalog

    def __init__(self, criterionCatalog: CriterionCatalog) -> None: ...
    def computeSuitabilityScore(
        self,
        subzone: Subzone,
        profile: PreferenceProfile,
        commute: CommuteEstimate,
    ) -> float: ...
    def computeCriterionScores(
        self,
        subzone: Subzone,
        profile: PreferenceProfile,
        commute: CommuteEstimate,
    ) -> list[CriterionScore]: ...
