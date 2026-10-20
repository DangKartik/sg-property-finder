from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from adapter.one_map_api_adapter import OneMapApiAdapter
    from entity.commute_estimate import CommuteEstimate
    from entity.types import Coordinates
    from entity.types import TransitMode


class CommuteControl:
    """«control» Calculates commute time and distance through the OneMap adapter."""

    apiAdapter: OneMapApiAdapter  # private

    def __init__(self, apiAdapter: OneMapApiAdapter) -> None:
        """Create a CommuteControl with its attributes (TODO: add validation if needed)."""
        self.apiAdapter = apiAdapter

    def calculateTravelTime(self, origin: Coordinates, dest: Coordinates, mode: TransitMode) -> CommuteEstimate:
        """Calculate travel time (public).

        Args:
            origin: Coordinates
            dest: Coordinates
            mode: TransitMode
        Returns:
            CommuteEstimate
        """
        raise NotImplementedError  # TODO
