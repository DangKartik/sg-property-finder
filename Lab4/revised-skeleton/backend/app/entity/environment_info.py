"""Environment info module."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from app.entity.enums import EnvironmentGranularity

@dataclass
class EnvironmentInfo:
    """Stereotype: Entity. Entity value object representing static and live environmental conditions."""
    weatherPattern: str
    greenCoveragePercent: float
    pm25: float | None = None
    uvi: float | None = None
    forecastCode: str | None = None
    granularity: EnvironmentGranularity = EnvironmentGranularity.REGION
    asOf: datetime | None = None

    def getWeatherPattern(self) -> str:
        """Return weather pattern.

        Args:
            None.

        Returns:
            str.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getGreenCoveragePercent(self) -> float:
        """Return green coverage percent.

        Args:
            None.

        Returns:
            float.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getPm25(self) -> float | None:
        """Return pm25.

        Args:
            None.

        Returns:
            float | None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getUvi(self) -> float | None:
        """Return uvi.

        Args:
            None.

        Returns:
            float | None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getGranularity(self) -> EnvironmentGranularity:
        """Return granularity.

        Args:
            None.

        Returns:
            EnvironmentGranularity.

        Failure handling:
            Not applicable at the skeleton level."""
        ...
