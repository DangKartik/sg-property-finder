"""Commute estimate entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.entity.enums import TransitMode


@dataclass
class CommuteEstimate:
    """Stereotype: Entity. Commute duration, distance, transfers and route."""

    durationMinutes: int
    distanceKm: float
    transferCount: int
    travelMode: TransitMode
    departureTime: datetime | None = None
    routeGeometry: str | None = None

    def getDurationMinutes(self) -> int:
        """Return duration in minutes."""
        return self.durationMinutes

    def getDistanceKm(self) -> float:
        """Return distance in kilometres."""
        return self.distanceKm

    def getTransferCount(self) -> int:
        """Return the number of transfers."""
        return self.transferCount
