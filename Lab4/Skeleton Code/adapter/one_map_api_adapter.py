from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.entity.types import Coordinates


class OneMapApiAdapter:
    """«adapter»"""

    apiKey: str
    baseUrl: str

    def getRoutingData(self, origin: Coordinates, dest: Coordinates, mode: str) -> dict:
        raise NotImplementedError  # TODO

    def getBasemapTile(self, x: int, y: int, zoom: int) -> bytes:
        raise NotImplementedError  # TODO
