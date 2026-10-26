"""Preference profile entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.entity.criterion_weight import CriterionWeight
    from app.entity.enums import TransitMode
    from app.entity.types import Coordinates


@dataclass
class PreferenceProfile:
    """Stereotype: Entity. A saved preference profile and its 1–10 criterion ratings."""

    profileId: str
    profileName: str
    budgetMin: float
    budgetMax: float
    selectedFlatTypes: list[str]
    workplaceAddress: str
    anchorCoordinates: Coordinates
    creationTime: datetime
    lastUpdatedTime: datetime
    isActive: bool
    criteriaWeights: list[CriterionWeight]
    preferredCommuteMode: TransitMode
    minimumPrimarySchools: int = 0
    minimumSecondarySchools: int = 0
    minimumTertiarySchools: int = 0
    minimumMalls: int = 0
    minimumHospitals: int = 0

    def getProfileId(self) -> str:
        """Return the profile identifier."""
        return self.profileId

    def getWeightForCriterion(self, criterionId: str) -> float:
        """Return the 1–10 importance rating for a criterion, or 0.0 if absent."""
        for weight in self.criteriaWeights:
            if weight.getCriterionId() == criterionId:
                return weight.getWeightValue()
        return 0.0
