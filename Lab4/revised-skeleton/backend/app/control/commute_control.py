from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.adapter.one_map_api_adapter import OneMapApiAdapter
    from app.entity.commute_estimate import CommuteEstimate
    from app.entity.types import Coordinates, TransitMode


class CommuteControl:
    oneMapAdapter: OneMapApiAdapter

    def __init__(self, oneMapAdapter: OneMapApiAdapter) -> None: ...
    def retrieveCommute(
        self,
        origin: Coordinates,
        destination: Coordinates,
        mode: TransitMode,
        departureTime: datetime | None = None,
    ) -> CommuteEstimate: ...
