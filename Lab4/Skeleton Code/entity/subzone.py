from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.entity.types import Polygon


class Subzone:
    """«entity»"""

    subzoneCode: str
    subzoneName: str
    boundaryPolygon: Polygon
    suitabilityScore: float

    def getSubzoneCode(self) -> str:
        raise NotImplementedError  # TODO

    def getSubzoneName(self) -> str:
        raise NotImplementedError  # TODO

    def setSuitabilityScore(self, score: float) -> None:
        raise NotImplementedError  # TODO

    def getSuitabilityScore(self) -> float:
        raise NotImplementedError  # TODO
