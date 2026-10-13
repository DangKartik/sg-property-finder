from __future__ import annotations

from sgpropfinder.control.retrieval_control import RetrievalControl
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.entity.house_pricing import HousePricing
    from sgpropfinder.entity.types import RawResponse


class HousePricingRetrievalControl(RetrievalControl):
    """«control»"""

    def retrieveHousePricing(self, subzoneCode: str) -> HousePricing:
        raise NotImplementedError  # TODO

    def parseResponse(self, data: RawResponse) -> HousePricing:
        raise NotImplementedError  # TODO
