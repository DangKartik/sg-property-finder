from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shapely.geometry import Polygon

    from app.entity.subzone_indicators import SubzoneIndicators
    from app.entity.types import Coordinates


@dataclass
class Subzone:
    subzoneCode: str
    subzoneName: str
    planningAreaName: str
    townName: str
    boundaryPolygon: Polygon
    regionName: str
    centroid: Coordinates
    indicators: SubzoneIndicators | None = None

    def getSubzoneCode(self) -> str: ...
    def getSubzoneName(self) -> str: ...
    def getTownName(self) -> str: ...
