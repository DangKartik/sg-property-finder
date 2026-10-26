"""Scoring strategy module."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.entity.commute_estimate import CommuteEstimate
    from app.entity.preference_profile import PreferenceProfile
    from app.entity.subzone import Subzone

class ScoringStrategy(ABC):
    """Stereotype: Strategy. Abstract strategy interface for computing suitability scores."""

    @abstractmethod
    def computeSuitabilityScore(self, subzone: Subzone, profile: PreferenceProfile, commute: CommuteEstimate) -> float:
        """Compute the 0–100 suitability score using available criteria.

        Args:
            subzone: Subzone
            profile: PreferenceProfile
            commute: CommuteEstimate

        Returns:
            float.

        Failure handling:
            Not applicable at the skeleton level."""
        ...
