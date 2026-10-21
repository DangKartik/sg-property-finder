"""Weighted scoring strategy module."""

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
    """Stereotype: Strategy. Concrete strategy implementing weighted multi-criteria suitability scoring."""
    criterionCatalog: CriterionCatalog

    def __init__(self, criterionCatalog: CriterionCatalog) -> None:
        """Initialise the WeightedScoringStrategy with its dependencies.

        Args:
            criterionCatalog: CriterionCatalog

        Returns:
            None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def computeSuitabilityScore(self, subzone: Subzone, profile: PreferenceProfile, commute: CommuteEstimate) -> float:
        """Compute the weighted 0–100 score after budget filtering and renormalisation.

        Args:
            subzone: Subzone
            profile: PreferenceProfile
            commute: CommuteEstimate

        Returns:
            float.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def computeCriterionScores(self, subzone: Subzone, profile: PreferenceProfile, commute: CommuteEstimate) -> list[CriterionScore]:
        """Return normalised, weighted CriterionScore rows and missing-data flags.

        Args:
            subzone: Subzone
            profile: PreferenceProfile
            commute: CommuteEstimate

        Returns:
            list[CriterionScore].

        Failure handling:
            Not applicable at the skeleton level."""
        ...
