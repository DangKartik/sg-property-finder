from __future__ import annotations

from control.retrieval_control import RetrievalControl

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entity.amenity_info import AmenityInfo
    from entity.types import RawResponse


class HousePricingRetrievalControl(RetrievalControl):
    """«control» Retrieves and parses house pricing data for a subzone."""

    def parseResponse(self, data: RawResponse) -> list[AmenityInfo]:
        """Parse response (protected).

        Args:
            data: RawResponse
        Returns:
            list[AmenityInfo]
        Note: Diagram shows List<AmenityInfo> here; HousePricing is probably intended.
        """
        raise NotImplementedError  # TODO

    def fetchPricingForSubzone(self, subzoneId: str) -> list[AmenityInfo]:
        """Fetch pricing for subzone (public).

        Args:
            subzoneId: str
        Returns:
            list[AmenityInfo]
        Note: Diagram shows List<AmenityInfo> here; HousePricing is probably intended.
        """
        raise NotImplementedError  # TODO
