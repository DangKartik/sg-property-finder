"""Preference profile module."""

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
    """Stereotype: Entity. Entity representing a saved preference profile and its criterion weights."""
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
        """Return profile id.

        Args:
            None.

        Returns:
            str.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def updateDetails(self, data: ProfileDTO) -> None:
        """Update details.

        Args:
            data: ProfileDTO

        Returns:
            None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def addCriterionWeight(self, weight: CriterionWeight) -> None:
        """Add criterion weight.

        Args:
            weight: CriterionWeight

        Returns:
            None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getCriteriaWeights(self) -> list[CriterionWeight]:
        """Return criteria weights.

        Args:
            None.

        Returns:
            list[CriterionWeight].

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getWeightForCriterion(self, criterionId: str) -> float:
        """Return weight for criterion.

        Args:
            criterionId: str

        Returns:
            float.

        Failure handling:
            Not applicable at the skeleton level."""
        ...
