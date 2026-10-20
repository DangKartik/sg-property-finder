from __future__ import annotations


class EnvironmentInfo:
    """«entity» Environmental quality figures for a subzone."""

    airQualityIndex: int  # private
    greenSpacePercentage: float  # private
    averageNoiseLevelDb: float  # private

    def __init__(self, airQualityIndex: int, greenSpacePercentage: float, averageNoiseLevelDb: float) -> None:
        """Create a EnvironmentInfo with its attributes (TODO: add validation if needed)."""
        self.airQualityIndex = airQualityIndex
        self.greenSpacePercentage = greenSpacePercentage
        self.averageNoiseLevelDb = averageNoiseLevelDb

    def getGreenSpace(self) -> float:
        """Get green space (public).

        Returns:
            float
        """
        raise NotImplementedError  # TODO
