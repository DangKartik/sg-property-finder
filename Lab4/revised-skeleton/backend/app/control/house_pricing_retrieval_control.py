from __future__ import annotations

from typing import TYPE_CHECKING

from app.control.retrieval_control import RetrievalControl

if TYPE_CHECKING:
    from app.entity.house_pricing import HousePricing
    from app.entity.types import RawResponse, RetrievalResult


class HousePricingRetrievalControl(RetrievalControl):
    def retrieveHousePricing(
        self,
        subzoneCode: str,
        flatTypes: list[str] | None = None,
    ) -> RetrievalResult[dict[str, HousePricing]]: ...
    def fetchData(self, resourceId: str) -> RawResponse: ...
    def parseResponse(self, data: RawResponse) -> dict[str, HousePricing]: ...
