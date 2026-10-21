"""Profile dto module."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.entity.criterion_weight import CriterionWeight
    from app.entity.enums import TransitMode
    from app.entity.types import Coordinates

@dataclass
class ProfileDTO:
    """Stereotype: Schema DTO. Schema DTO carrying preference-profile input to the backend."""
    profileId: str | None
    profileName: str
    budgetMin: float
    budgetMax: float
    selectedFlatTypes: list[str]
    workplaceAddress: str | None
    anchorCoordinates: Coordinates | None
    criteriaWeights: list[CriterionWeight]
    preferredCommuteMode: TransitMode
    departureTime: datetime | None = None
    isActive: bool = True
    creationTime: datetime | None = None
    lastUpdatedTime: datetime | None = None
