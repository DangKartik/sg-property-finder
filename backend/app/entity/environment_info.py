"""Environment information entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.entity.enums import EnvironmentGranularity


@dataclass
class EnvironmentInfo:
    """Stereotype: Entity. Static and live environmental information."""

    weatherPattern: str
    greenCoveragePercent: float
    pm25: float | None = None
    uvi: float | None = None
    forecastCode: str | None = None
    granularity: EnvironmentGranularity = EnvironmentGranularity.REGION
    asOf: datetime | None = None

    def getWeatherPattern(self) -> str:
        """Return the weather pattern label."""
        return self.weatherPattern

    def getGreenCoveragePercent(self) -> float:
        """Return green coverage percentage."""
        return self.greenCoveragePercent

    def getPm25(self) -> float | None:
        """Return the live PM2.5 value, when available."""
        return self.pm25

    def getUvi(self) -> float | None:
        """Return the live UVI value, when available."""
        return self.uvi

    def getGranularity(self) -> EnvironmentGranularity:
        """Return the data granularity."""
        return self.granularity
