"""Subzone module."""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from shapely.geometry import Polygon
    from app.entity.subzone_indicators import SubzoneIndicators
    from app.entity.types import Coordinates

@dataclass
class Subzone:
    """Stereotype: Entity. Entity representing one URA subzone, its HDB town, boundary and derived indicators."""
    subzoneCode: str
    subzoneName: str
    planningAreaName: str
    townName: str
    boundaryPolygon: Polygon
    regionName: str
    centroid: Coordinates
    indicators: SubzoneIndicators | None = None

    def getSubzoneCode(self) -> str:
        """Return subzone code.

        Args:
            None.

        Returns:
            str.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getSubzoneName(self) -> str:
        """Return subzone name.

        Args:
            None.

        Returns:
            str.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getTownName(self) -> str:
        """Return town name.

        Args:
            None.

        Returns:
            str.

        Failure handling:
            Not applicable at the skeleton level."""
        ...
