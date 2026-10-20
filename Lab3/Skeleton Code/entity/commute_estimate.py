from __future__ import annotations


class CommuteEstimate:
    """«entity» Estimated commute from the workplace to a subzone."""

    durationMinutes: int  # private
    transitMode: str  # private
    distanceKm: float  # private

    def __init__(self, durationMinutes: int, transitMode: str, distanceKm: float) -> None:
        """Create a CommuteEstimate with its attributes (TODO: add validation if needed)."""
        self.durationMinutes = durationMinutes
        self.transitMode = transitMode
        self.distanceKm = distanceKm

    def getDuration(self) -> int:
        """Get duration (public).

        Returns:
            int
        """
        raise NotImplementedError  # TODO

    def getMode(self) -> str:
        """Get mode (public).

        Returns:
            str
        """
        raise NotImplementedError  # TODO
