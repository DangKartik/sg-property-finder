"""Preference profile entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.entity.criterion_weight import CriterionWeight
    from app.entity.enums import TransitMode
    from app.entity.types import Coordinates
    from app.schemas.profile_dto import ProfileDTO


@dataclass
class PreferenceProfile:
    """Stereotype: Entity. A saved preference profile and its criterion weights."""

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

    def getProfileId(self) -> str:
        """Return the profile identifier."""
        return self.profileId

    def updateDetails(self, data: ProfileDTO) -> None:
        """Copy non-null fields from a profile DTO and update the timestamp."""
        self.profileName = data.profileName
        self.budgetMin = data.budgetMin
        self.budgetMax = data.budgetMax
        self.selectedFlatTypes = list(data.selectedFlatTypes)
        if data.workplaceAddress is not None:
            self.workplaceAddress = data.workplaceAddress
        if data.anchorCoordinates is not None:
            self.anchorCoordinates = data.anchorCoordinates
        self.criteriaWeights = list(data.criteriaWeights)
        self.preferredCommuteMode = data.preferredCommuteMode
        self.isActive = data.isActive
        self.lastUpdatedTime = datetime.now()

    def addCriterionWeight(self, weight: CriterionWeight) -> None:
        """Add or replace the weight for a criterion."""
        for index, existing in enumerate(self.criteriaWeights):
            if existing.getCriterionId() == weight.getCriterionId():
                self.criteriaWeights[index] = weight
                return
        self.criteriaWeights.append(weight)

    def getCriteriaWeights(self) -> list[CriterionWeight]:
        """Return the profile's criterion weights."""
        return list(self.criteriaWeights)

    def getWeightForCriterion(self, criterionId: str) -> float:
        """Return the weight for a criterion, or 0.0 when not configured."""
        for weight in self.criteriaWeights:
            if weight.getCriterionId() == criterionId:
                return weight.getWeightValue()
        return 0.0
