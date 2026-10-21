"""House pricing module."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass
class HousePricing:
    """Stereotype: Entity. Entity value object representing HDB resale pricing for one flat type."""
    averagePrice: float
    medianPricePerSqm: float
    priceTrend: str
    priceTrendPercent: float
    flatType: str
    transactionCount: int
    isTownProxy: bool = False
    dataWindowMonths: int = 12
    asOf: datetime | None = None

    def getAveragePrice(self) -> float:
        """Return average price.

        Args:
            None.

        Returns:
            float.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getMedianPricePerSqm(self) -> float:
        """Return median price per sqm.

        Args:
            None.

        Returns:
            float.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getPriceTrend(self) -> str:
        """Return price trend.

        Args:
            None.

        Returns:
            str.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getPriceTrendPercent(self) -> float:
        """Return price trend percent.

        Args:
            None.

        Returns:
            float.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getIsTownProxy(self) -> bool:
        """Return is town proxy.

        Args:
            None.

        Returns:
            bool.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getTransactionCount(self) -> int:
        """Return transaction count.

        Args:
            None.

        Returns:
            int.

        Failure handling:
            Not applicable at the skeleton level."""
        ...
