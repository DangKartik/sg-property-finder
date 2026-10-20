from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from adapter.one_map_api_adapter import OneMapApiAdapter
    from container.subzone_registry import SubzoneRegistry
    from control.commute_control import CommuteControl
    from entity.types import Coordinates
    from entity.types import MapData
    from entity.types import RouteData


class MapControl:
    """«control» Prepares map data (subzone polygons, commute overlay) for the map UI."""

    subzoneRegistry: SubzoneRegistry  # private
    commuteControl: CommuteControl  # private
    mapAdapter: OneMapApiAdapter  # private

    def __init__(self, subzoneRegistry: SubzoneRegistry, commuteControl: CommuteControl, mapAdapter: OneMapApiAdapter) -> None:
        """Create a MapControl with its attributes (TODO: add validation if needed)."""
        self.subzoneRegistry = subzoneRegistry
        self.commuteControl = commuteControl
        self.mapAdapter = mapAdapter

    def getSubzonePolygons(self) -> MapData:
        """Get subzone polygons (public).

        Returns:
            MapData
        """
        raise NotImplementedError  # TODO

    def getCommuteOverlay(self, start: Coordinates, dest: Coordinates) -> RouteData:
        """Get commute overlay (public).

        Args:
            start: Coordinates
            dest: Coordinates
        Returns:
            RouteData
        """
        raise NotImplementedError  # TODO
