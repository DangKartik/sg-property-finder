from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.entity.types import Coordinates


@dataclass
class AmenityInfo:
    amenityName: str
    category: str
    location: Coordinates
    distanceKm: float | None = None

    def getAmenityName(self) -> str: ...
    def getCategory(self) -> str: ...
    def getDistanceKm(self) -> float | None: ...
