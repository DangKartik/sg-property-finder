from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.entity.amenity_info import AmenityInfo
    from app.entity.commute_estimate import CommuteEstimate
    from app.entity.environment_info import EnvironmentInfo
    from app.entity.house_pricing import HousePricing
    from app.entity.subzone_indicators import SubzoneIndicators
    from app.schemas.data_availability_warning import DataAvailabilityWarning


@dataclass
class NeighborhoodDetailDTO:
    subzoneCode: str
    subzoneName: str
    pricing: dict[str, HousePricing]
    amenities: list[AmenityInfo]
    environment: EnvironmentInfo
    commute: CommuteEstimate
    warnings: list[DataAvailabilityWarning]
    generatedTime: datetime
    indicators: SubzoneIndicators | None = None
