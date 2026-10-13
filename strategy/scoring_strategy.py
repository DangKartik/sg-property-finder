from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.entity.commute_estimate import CommuteEstimate
    from sgpropfinder.entity.preference_profile import PreferenceProfile
    from sgpropfinder.entity.subzone import Subzone


class ScoringStrategy(ABC):
    """«strategy»"""

    @abstractmethod
    def computeSuitabilityScore(self, subzone: Subzone, profile: PreferenceProfile, commute: CommuteEstimate) -> float:
        ...
