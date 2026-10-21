from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.control.amenity_retrieval_control import AmenityRetrievalControl
    from app.control.commute_control import CommuteControl
    from app.control.environment_retrieval_control import EnvironmentRetrievalControl
    from app.control.house_pricing_retrieval_control import HousePricingRetrievalControl
    from app.entity.preference_profile import PreferenceProfile
    from app.schemas.neighborhood_detail_dto import NeighborhoodDetailDTO


class NeighborhoodDetailsControl:
    amenityControl: AmenityRetrievalControl
    envControl: EnvironmentRetrievalControl
    pricingControl: HousePricingRetrievalControl
    commuteControl: CommuteControl

    def __init__(
        self,
        amenityControl: AmenityRetrievalControl,
        envControl: EnvironmentRetrievalControl,
        pricingControl: HousePricingRetrievalControl,
        commuteControl: CommuteControl,
    ) -> None: ...
    def fetchNeighborhoodDetails(
        self,
        subzoneCode: str,
        profile: PreferenceProfile,
    ) -> NeighborhoodDetailDTO: ...
