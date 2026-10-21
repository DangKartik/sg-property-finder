"""Amenity retrieval control module."""

from __future__ import annotations
from typing import TYPE_CHECKING
from app.control.retrieval_control import RetrievalControl
if TYPE_CHECKING:
    from app.entity.amenity_info import AmenityInfo
    from app.entity.types import RawResponse, RetrievalResult

class AmenityRetrievalControl(RetrievalControl):
    """Stereotype: Control. Control that retrieves and parses amenity datasets for a subzone."""

    def retrieveAmenityInfo(self, subzoneCode: str) -> RetrievalResult[list[AmenityInfo]]:
        """Return amenities near a subzone and any warnings.

        Args:
            subzoneCode: str

        Returns:
            RetrievalResult[list[AmenityInfo]].

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def fetchData(self, resourceId: str) -> RawResponse:
        """Fetch data; surface failures to the caller.

        Args:
            resourceId: str

        Returns:
            RawResponse.

        Failure handling:
            Raise a typed error or return a warning/result; do not retain shared state."""
        ...

    def parseResponse(self, data: RawResponse) -> list[AmenityInfo]:
        """Parse response into domain objects.

        Args:
            data: RawResponse

        Returns:
            list[AmenityInfo].

        Failure handling:
            Not applicable at the skeleton level."""
        ...
