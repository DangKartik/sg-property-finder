from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entity.amenity_info import AmenityInfo
    from entity.commute_estimate import CommuteEstimate
    from entity.environment_info import EnvironmentInfo
    from entity.house_pricing import HousePricing


class Subzone:
    """«entity» A Singapore subzone with its boundary, amenities, commute estimates, pricing and environment data."""

    subzoneId: str  # private
    name: str  # private
    boundariesGeoJson: str  # private
    amenities: list[AmenityInfo]  # private
    commuteEstimates: list[CommuteEstimate]  # private
    pricing: HousePricing  # private
    environment: EnvironmentInfo  # private

    def __init__(self, subzoneId: str, name: str, boundariesGeoJson: str, amenities: list[AmenityInfo], commuteEstimates: list[CommuteEstimate], pricing: HousePricing, environment: EnvironmentInfo) -> None:
        """Create a Subzone with its attributes (TODO: add validation if needed)."""
        self.subzoneId = subzoneId
        self.name = name
        self.boundariesGeoJson = boundariesGeoJson
        self.amenities = amenities
        self.commuteEstimates = commuteEstimates
        self.pricing = pricing
        self.environment = environment

    def getId(self) -> str:
        """Get id (public).

        Returns:
            str
        """
        raise NotImplementedError  # TODO

    def addAmenity(self, amenity: AmenityInfo) -> None:
        """Add amenity (public).

        Args:
            amenity: AmenityInfo
        """
        raise NotImplementedError  # TODO

    def setHousePricing(self, pricing: HousePricing) -> None:
        """Set house pricing (public).

        Args:
            pricing: HousePricing
        """
        raise NotImplementedError  # TODO
