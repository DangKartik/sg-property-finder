"""Commute estimate module."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from app.entity.enums import TransitMode

@dataclass
class CommuteEstimate:
    """Stereotype: Entity. Entity value object representing a commute duration, distance and transfer count."""
    durationMinutes: int
    distanceKm: float
    transferCount: int
    travelMode: TransitMode
    departureTime: datetime | None = None
    routeGeometry: str | None = None

    def getDurationMinutes(self) -> int:
        """Return duration minutes.

        Args:
            None.

        Returns:
            int.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getDistanceKm(self) -> float:
        """Return distance km.

        Args:
            None.

        Returns:
            float.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getTransferCount(self) -> int:
        """Return transfer count.

        Args:
            None.

        Returns:
            int.

        Failure handling:
            Not applicable at the skeleton level."""
        ...
