from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.control.commute_control import CommuteControl
    from sgpropfinder.adapter.one_map_api_adapter import OneMapApiAdapter
    from sgpropfinder.entity.types import Polygon
    from sgpropfinder.entity.subzone import Subzone
    from sgpropfinder.container.subzone_registry import SubzoneRegistry


class MapControl:
    """«control»"""

    subzoneRegistry: SubzoneRegistry
    oneMapAdapter: OneMapApiAdapter
    commuteControl: CommuteControl

    def generateMapData(self) -> list[Subzone]:
        raise NotImplementedError  # TODO

    def fetchSubzoneBoundary(self, subzoneCode: str) -> Polygon:
        raise NotImplementedError  # TODO
