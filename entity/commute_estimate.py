from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class CommuteEstimate:
    """«entity»"""

    durationMinutes: int
    distanceKm: float
    transferCount: int
    travelMode: str

    def getDurationMinutes(self) -> int:
        raise NotImplementedError  # TODO

    def getDistanceKm(self) -> float:
        raise NotImplementedError  # TODO

    def getTransferCount(self) -> int:
        raise NotImplementedError  # TODO
