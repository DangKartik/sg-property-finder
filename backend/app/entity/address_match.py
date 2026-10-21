"""Address match entity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.entity.types import Coordinates


@dataclass
class AddressMatch:
    """Stereotype: Entity. A detailed OneMap address match."""

    formattedAddress: str
    postalCode: str
    coordinates: Coordinates
    confidenceScore: float | None = None

    def getFormattedAddress(self) -> str:
        """Return the formatted address."""
        return self.formattedAddress

    def getPostalCode(self) -> str:
        """Return the postal code."""
        return self.postalCode

    def getCoordinates(self) -> Coordinates:
        """Return the matched coordinates."""
        return self.coordinates

    def getConfidenceScore(self) -> float | None:
        """Return the optional confidence score."""
        return self.confidenceScore
