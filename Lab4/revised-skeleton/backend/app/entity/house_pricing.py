"""House pricing entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class HousePricing:
    """Stereotype: Entity. HDB resale pricing for one flat type."""

    averagePrice: float
    medianPricePerSqm: float
    priceTrend: str
    priceTrendPercent: float
    flatType: str
    transactionCount: int
    isTownProxy: bool = False
    dataWindowMonths: int = 12
    asOf: datetime | None = None
    medianPrice: float | None = None

    def getAveragePrice(self) -> float:
        """Return average resale price."""
        return self.averagePrice

    def getMedianPrice(self) -> float | None:
        """Return median resale price when available."""
        return self.medianPrice if self.medianPrice is not None else self.averagePrice

    def getMedianPricePerSqm(self) -> float:
        """Return median price per square metre."""
        return self.medianPricePerSqm

    def getPriceTrend(self) -> str:
        """Return the descriptive price trend."""
        return self.priceTrend

    def getPriceTrendPercent(self) -> float:
        """Return the numeric price trend percentage."""
        return self.priceTrendPercent

    def getIsTownProxy(self) -> bool:
        """Return whether the price uses the HDB-town proxy."""
        return self.isTownProxy

    def getTransactionCount(self) -> int:
        """Return the number of transactions in the window."""
        return self.transactionCount
