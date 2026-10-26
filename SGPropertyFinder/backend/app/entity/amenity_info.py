"""Amenity entity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.entity.types import Coordinates


@dataclass
class AmenityInfo:
    """Stereotype: Entity. An amenity and its distance from a subzone."""

    amenityName: str
    category: str
    location: Coordinates
    distanceKm: float | None = None

    def getAmenityName(self) -> str:
        """Return the amenity name."""
        return self.amenityName

    def getCategory(self) -> str:
        """Return the amenity category."""
        return self.category

    def getDistanceKm(self) -> float | None:
        """Return distance from the subzone anchor in kilometres."""
        return self.distanceKm
