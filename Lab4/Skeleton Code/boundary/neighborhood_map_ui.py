from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from control.map_control import MapControl
    from entity.commute_estimate import CommuteEstimate
    from entity.subzone import Subzone


class NeighborhoodMapUI:
    """«boundary» Interactive map of subzones with the commute route layer."""

    mapControl: MapControl  # private

    def __init__(self, mapControl: MapControl) -> None:
        """Create a NeighborhoodMapUI with its attributes (TODO: add validation if needed)."""
        self.mapControl = mapControl

    def renderMap(self, subzones: list[Subzone]) -> None:
        """Render map (public).

        Args:
            subzones: list[Subzone]
        """
        raise NotImplementedError  # TODO

    def renderCommuteLayer(self, routes: list[CommuteEstimate]) -> None:
        """Render commute layer (public).

        Args:
            routes: list[CommuteEstimate]
        """
        raise NotImplementedError  # TODO
