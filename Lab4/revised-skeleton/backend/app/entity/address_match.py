"""Address match module."""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.entity.types import Coordinates

@dataclass
class AddressMatch:
    """Stereotype: Entity. Entity value object representing an address match returned by OneMap."""
    formattedAddress: str
    postalCode: str
    coordinates: Coordinates
    confidenceScore: float | None = None

    def getFormattedAddress(self) -> str:
        """Return formatted address.

        Args:
            None.

        Returns:
            str.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getPostalCode(self) -> str:
        """Return postal code.

        Args:
            None.

        Returns:
            str.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getCoordinates(self) -> Coordinates:
        """Return coordinates.

        Args:
            None.

        Returns:
            Coordinates.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getConfidenceScore(self) -> float | None:
        """Return confidence score.

        Args:
            None.

        Returns:
            float | None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...
