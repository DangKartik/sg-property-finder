from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class HousePricing:
    averagePrice: float
    medianPricePerSqm: float
    priceTrend: str
    priceTrendPercent: float
    flatType: str
    transactionCount: int
    isTownProxy: bool = False
    dataWindowMonths: int = 12
    asOf: datetime | None = None

    def getAveragePrice(self) -> float: ...
    def getMedianPricePerSqm(self) -> float: ...
    def getPriceTrend(self) -> str: ...
    def getPriceTrendPercent(self) -> float: ...
    def getIsTownProxy(self) -> bool: ...
    def getTransactionCount(self) -> int: ...
