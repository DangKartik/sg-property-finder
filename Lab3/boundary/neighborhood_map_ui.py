from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.entity.commute_estimate import CommuteEstimate
    from sgpropfinder.entity.types import Coordinates
    from sgpropfinder.entity.subzone import Subzone


class NeighborhoodMapUI:
    """«boundary»"""

    choroplethLayers: dict[str, object]
    mapCenterCoordinates: Coordinates

    def renderMap(self, subzones: list[Subzone]) -> None:
        raise NotImplementedError  # TODO

    def highlightSubzone(self, subzoneId: str) -> None:
        raise NotImplementedError  # TODO

    def renderCommuteOverlay(self, estimate: CommuteEstimate) -> None:
        raise NotImplementedError  # TODO
