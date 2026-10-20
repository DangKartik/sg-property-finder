from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.control.amenity_retrieval_control import AmenityRetrievalControl
    from sgpropfinder.control.commute_control import CommuteControl
    from sgpropfinder.control.environment_retrieval_control import EnvironmentRetrievalControl
    from sgpropfinder.control.house_pricing_retrieval_control import HousePricingRetrievalControl
    from sgpropfinder.entity.types import NeighborhoodDetailDTO


class NeighborhoodDetailsControl:
    """«control»"""

    amenityControl: AmenityRetrievalControl
    envControl: EnvironmentRetrievalControl
    pricingControl: HousePricingRetrievalControl
    commuteControl: CommuteControl

    def fetchNeighborhoodDetails(self, subzoneCode: str, profileId: str) -> NeighborhoodDetailDTO:
        raise NotImplementedError  # TODO
