from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.entity.criterion_weight import CriterionWeight
    from app.entity.types import Coordinates, TransitMode
    from app.schemas.profile_dto import ProfileDTO


@dataclass
class PreferenceProfile:
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

    def getProfileId(self) -> str: ...
    def updateDetails(self, data: ProfileDTO) -> None: ...
    def addCriterionWeight(self, weight: CriterionWeight) -> None: ...
    def getCriteriaWeights(self) -> list[CriterionWeight]: ...
    def getWeightForCriterion(self, criterionId: str) -> float: ...
