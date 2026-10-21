"""Map control module."""

from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from shapely.geometry import Polygon
    from app.adapter.one_map_api_adapter import OneMapApiAdapter
    from app.container.subzone_registry import SubzoneRegistry
    from app.control.commute_control import CommuteControl
    from app.entity.enums import TransitMode
    from app.entity.types import Coordinates, MapData, RouteData

class MapControl:
    """Stereotype: Control. Control that prepares map payloads and commute overlays for the UI."""
    subzoneRegistry: SubzoneRegistry
    oneMapAdapter: OneMapApiAdapter
    commuteControl: CommuteControl

    def __init__(self, subzoneRegistry: SubzoneRegistry, oneMapAdapter: OneMapApiAdapter, commuteControl: CommuteControl) -> None:
        """Initialise the MapControl with its dependencies.

        Args:
            subzoneRegistry: SubzoneRegistry
            oneMapAdapter: OneMapApiAdapter
            commuteControl: CommuteControl

        Returns:
            None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def generateMapData(self) -> MapData:
        """Return GeoJSON, total scores and the map center for the choropleth.

        Args:
            None.

        Returns:
            MapData.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def fetchSubzoneBoundary(self, subzoneCode: str) -> Polygon:
        """Return the Shapely polygon for a subzone; raise if the code is unknown.

        Args:
            subzoneCode: str

        Returns:
            Polygon.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getCommuteOverlay(self, origin: Coordinates, destination: Coordinates, mode: TransitMode, departureTime: datetime | None=None) -> RouteData:
        """Return route geometry for the map; OneMap failures propagate as typed errors.

        Args:
            origin: Coordinates
            destination: Coordinates
            mode: TransitMode
            departureTime: datetime | None

        Returns:
            RouteData.

        Failure handling:
            Not applicable at the skeleton level."""
        ...
