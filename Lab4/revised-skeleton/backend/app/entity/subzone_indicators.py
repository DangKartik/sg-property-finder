"""Precomputed subzone indicators."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SubzoneIndicators:
    """Stereotype: Entity. Numeric features consumed by scoring."""

    nearestParkM: float | None = None
    parkCount500m: int = 0
    greenCoveragePercent500m: float | None = None
    nearestSchoolM: float | None = None
    primarySchoolCount1km: int = 0
    secondarySchoolCount1km: int = 0
    nearestPolyclinicM: float | None = None
    polyclinicCount2km: int = 0
    nearestHospitalM: float | None = None
    hospitalCount2km: int = 0
    nearestMallM: float | None = None
    mallCount1km: int = 0
    nearestMrtM: float | None = None
    mrtStationCount800m: int = 0
    parkConnectorLength1km: float = 0.0
    cyclingPathLength1km: float = 0.0
    medianResalePrice: float | None = None
    medianPricePerSqm: float | None = None
    transactionCount12m: int = 0
    priceTrendPercent: float | None = None
    medianPriceByFlatType: dict[str, float] = field(default_factory=dict)
    transactionCountByFlatType: dict[str, int] = field(default_factory=dict)
    pm25Baseline: float | None = None
    pm25Live: float | None = None
    uvi: float | None = None
    forecastCode: str | None = None
    dataAsOf: datetime | None = None
