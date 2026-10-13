from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from sgpropfinder.entity.types import Coordinates
    from sgpropfinder.entity.criterion_weight import CriterionWeight
    from sgpropfinder.entity.types import ProfileDTO


class PreferenceProfile:
    """«entity»"""

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

    def getProfileId(self) -> str:
        raise NotImplementedError  # TODO

    def updateDetails(self, data: ProfileDTO) -> None:
        raise NotImplementedError  # TODO

    def addCriterionWeight(self, weight: CriterionWeight) -> None:
        raise NotImplementedError  # TODO

    def getCriteriaWeights(self) -> list[CriterionWeight]:
        raise NotImplementedError  # TODO
