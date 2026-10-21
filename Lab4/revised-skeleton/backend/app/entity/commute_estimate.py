from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.entity.types import TransitMode


@dataclass
class CommuteEstimate:
    durationMinutes: int
    distanceKm: float
    transferCount: int
    travelMode: TransitMode
    departureTime: datetime | None = None
    routeGeometry: str | None = None

    def getDurationMinutes(self) -> int: ...
    def getDistanceKm(self) -> float: ...
    def getTransferCount(self) -> int: ...
