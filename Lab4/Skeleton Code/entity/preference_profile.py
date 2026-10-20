from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entity.criterion_weight import CriterionWeight


class PreferenceProfile:
    """«entity» A user's saved preferences and the weight given to each criterion."""

    profileId: str  # private
    profileName: str  # private
    criteriaWeights: list[CriterionWeight]  # private

    def __init__(self, profileId: str, profileName: str, criteriaWeights: list[CriterionWeight]) -> None:
        """Create a PreferenceProfile with its attributes (TODO: add validation if needed)."""
        self.profileId = profileId
        self.profileName = profileName
        self.criteriaWeights = criteriaWeights

    def getWeightForCriterion(self, criterion: str) -> float:
        """Get weight for criterion (public).

        Args:
            criterion: str
        Returns:
            float
        """
        raise NotImplementedError  # TODO

    def updateWeight(self, criterion: str, weight: float) -> None:
        """Update weight (public).

        Args:
            criterion: str
            weight: float
        """
        raise NotImplementedError  # TODO
