"""Subzone entity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.geometry import Polygon
    from app.entity.subzone_indicators import SubzoneIndicators
    from app.entity.types import Coordinates


@dataclass
class Subzone:
    """Stereotype: Entity. A URA subzone and its derived indicators."""

    subzoneCode: str
    subzoneName: str
    planningAreaName: str
    townName: str
    boundaryPolygon: Polygon
    regionName: str
    centroid: Coordinates
    indicators: SubzoneIndicators | None = None
    dataAvailable: bool = True

    def getSubzoneCode(self) -> str:
        """Return the subzone code."""
        return self.subzoneCode

    def getSubzoneName(self) -> str:
        """Return the subzone name."""
        return self.subzoneName

    def getTownName(self) -> str:
        """Return the HDB town join key."""
        return self.townName
