from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shapely.geometry import Polygon

    from app.adapter.one_map_api_adapter import OneMapApiAdapter
    from app.container.subzone_registry import SubzoneRegistry
    from app.control.commute_control import CommuteControl
    from app.entity.types import Coordinates, MapData, RouteData, TransitMode


class MapControl:
    subzoneRegistry: SubzoneRegistry
    oneMapAdapter: OneMapApiAdapter
    commuteControl: CommuteControl

    def __init__(
        self,
        subzoneRegistry: SubzoneRegistry,
        oneMapAdapter: OneMapApiAdapter,
        commuteControl: CommuteControl,
    ) -> None: ...
    def generateMapData(self) -> MapData: ...
    def fetchSubzoneBoundary(self, subzoneCode: str) -> Polygon: ...
    def getCommuteOverlay(
        self,
        origin: Coordinates,
        destination: Coordinates,
        mode: TransitMode,
        departureTime: datetime | None = None,
    ) -> RouteData: ...
