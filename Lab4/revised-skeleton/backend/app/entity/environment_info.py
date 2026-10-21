from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.entity.types import EnvironmentGranularity


@dataclass
class EnvironmentInfo:
    weatherPattern: str
    greenCoveragePercent: float
    pm25: float | None = None
    uvi: float | None = None
    forecastCode: str | None = None
    granularity: EnvironmentGranularity = EnvironmentGranularity.REGION
    asOf: datetime | None = None

    def getWeatherPattern(self) -> str: ...
    def getGreenCoveragePercent(self) -> float: ...
    def getPm25(self) -> float | None: ...
    def getUvi(self) -> float | None: ...
    def getGranularity(self) -> EnvironmentGranularity: ...
