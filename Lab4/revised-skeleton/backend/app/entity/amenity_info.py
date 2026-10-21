"""Amenity info module."""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.entity.types import Coordinates

@dataclass
class AmenityInfo:
    """Stereotype: Entity. Entity value object representing an amenity and its distance from a subzone."""
    amenityName: str
    category: str
    location: Coordinates
    distanceKm: float | None = None

    def getAmenityName(self) -> str:
        """Return amenity name.

        Args:
            None.

        Returns:
            str.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getCategory(self) -> str:
        """Return category.

        Args:
            None.

        Returns:
            str.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getDistanceKm(self) -> float | None:
        """Return distance km.

        Args:
            None.

        Returns:
            float | None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...
