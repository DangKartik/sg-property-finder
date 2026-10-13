from __future__ import annotations

from sgpropfinder.control.retrieval_control import RetrievalControl
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.entity.amenity_info import AmenityInfo
    from sgpropfinder.entity.types import RawResponse


class AmenityRetrievalControl(RetrievalControl):
    """«control»"""

    def retrieveAmenityInfo(self, subzoneCode: str) -> list[AmenityInfo]:
        raise NotImplementedError  # TODO

    def parseResponse(self, data: RawResponse) -> list[AmenityInfo]:
        raise NotImplementedError  # TODO
