from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.entity.types import Coordinates


class AmenityInfo:
    """«entity»"""

    amenityName: str
    category: str
    location: Coordinates

    def getAmenityName(self) -> str:
        raise NotImplementedError  # TODO

    def getCategory(self) -> str:
        raise NotImplementedError  # TODO
