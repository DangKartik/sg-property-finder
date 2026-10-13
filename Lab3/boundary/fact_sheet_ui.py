from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.entity.amenity_info import AmenityInfo
    from sgpropfinder.entity.commute_estimate import CommuteEstimate
    from sgpropfinder.entity.environment_info import EnvironmentInfo
    from sgpropfinder.entity.house_pricing import HousePricing


class FactSheetUI:
    """«boundary»"""

    activeSubzoneId: str

    def displayDetails(self, amenities: list[AmenityInfo], env: EnvironmentInfo, pricing: HousePricing, commute: CommuteEstimate) -> None:
        raise NotImplementedError  # TODO
