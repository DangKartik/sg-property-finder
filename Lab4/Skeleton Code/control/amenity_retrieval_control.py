from __future__ import annotations

from control.retrieval_control import RetrievalControl

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entity.amenity_info import AmenityInfo
    from entity.types import RawResponse


class AmenityRetrievalControl(RetrievalControl):
    """«control» Retrieves and parses amenity data for a subzone."""

    def parseResponse(self, data: RawResponse) -> list[AmenityInfo]:
        """Parse response (protected).

        Args:
            data: RawResponse
        Returns:
            list[AmenityInfo]
        """
        raise NotImplementedError  # TODO

    def fetchAmenitiesForSubzone(self, subzoneId: str) -> list[AmenityInfo]:
        """Fetch amenities for subzone (public).

        Args:
            subzoneId: str
        Returns:
            list[AmenityInfo]
        """
        raise NotImplementedError  # TODO
