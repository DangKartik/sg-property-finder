from __future__ import annotations

from abc import ABC, abstractmethod

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entity.preference_profile import PreferenceProfile
    from entity.subzone import Subzone


class ScoringStrategy(ABC):
    """«strategy» interface: Strategy interface for computing a subzone's suitability score."""

    @abstractmethod
    def calculateScore(self, subzone: Subzone, profile: PreferenceProfile) -> float:
        """Calculate score (public).

        Args:
            subzone: Subzone
            profile: PreferenceProfile
        Returns:
            float
        """
