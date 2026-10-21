from __future__ import annotations

from typing import TYPE_CHECKING

from app.control.retrieval_control import RetrievalControl

if TYPE_CHECKING:
    from app.entity.amenity_info import AmenityInfo
    from app.entity.types import RawResponse, RetrievalResult


class AmenityRetrievalControl(RetrievalControl):
    def retrieveAmenityInfo(self, subzoneCode: str) -> RetrievalResult[list[AmenityInfo]]: ...
    def fetchData(self, resourceId: str) -> RawResponse: ...
    def parseResponse(self, data: RawResponse) -> list[AmenityInfo]: ...
