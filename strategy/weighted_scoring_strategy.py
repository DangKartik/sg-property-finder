from __future__ import annotations

from sgpropfinder.strategy.scoring_strategy import ScoringStrategy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.entity.commute_estimate import CommuteEstimate
    from sgpropfinder.entity.preference_profile import PreferenceProfile
    from sgpropfinder.entity.subzone import Subzone


class WeightedScoringStrategy(ScoringStrategy):
    """«strategy»"""

    weightMap: dict[str, float]

    def computeSuitabilityScore(self, subzone: Subzone, profile: PreferenceProfile, commute: CommuteEstimate) -> float:
        raise NotImplementedError  # TODO
