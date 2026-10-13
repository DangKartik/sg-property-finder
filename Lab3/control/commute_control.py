from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.entity.commute_estimate import CommuteEstimate
    from sgpropfinder.entity.types import Coordinates
    from sgpropfinder.adapter.one_map_api_adapter import OneMapApiAdapter


class CommuteControl:
    """«control»"""

    oneMapAdapter: OneMapApiAdapter

    def retrieveCommute(self, origin: Coordinates, destination: Coordinates, mode: str) -> CommuteEstimate:
        raise NotImplementedError  # TODO
