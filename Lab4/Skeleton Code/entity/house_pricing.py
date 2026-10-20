from __future__ import annotations


class HousePricing:
    """«entity» House pricing figures for a subzone."""

    medianPrice: float  # private
    propertyType: str  # private
    pricePerSqFt: float  # private

    def __init__(self, medianPrice: float, propertyType: str, pricePerSqFt: float) -> None:
        """Create a HousePricing with its attributes (TODO: add validation if needed)."""
        self.medianPrice = medianPrice
        self.propertyType = propertyType
        self.pricePerSqFt = pricePerSqFt

    def getMedianPrice(self) -> float:
        """Get median price (public).

        Returns:
            float
        """
        raise NotImplementedError  # TODO
