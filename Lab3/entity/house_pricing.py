from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class HousePricing:
    """«entity»"""

    averagePrice: float
    medianPricePerSqm: float
    priceTrend: str

    def getAveragePrice(self) -> float:
        raise NotImplementedError  # TODO

    def getMedianPricePerSqm(self) -> float:
        raise NotImplementedError  # TODO
