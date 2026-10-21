from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, TypeAlias, TypeVar

if TYPE_CHECKING:
    from app.schemas.data_availability_warning import DataAvailabilityWarning

JSON: TypeAlias = dict[str, Any]
T = TypeVar("T")


@dataclass
class Coordinates:
    latitude: float
    longitude: float

    def toOneMapString(self) -> str: ...
    def toGeoJSON(self) -> tuple[float, float]: ...


class TransitMode(str, Enum):
    PUBLIC_TRANSIT = "PUBLIC_TRANSIT"
    DRIVING = "DRIVING"
    WALKING = "WALKING"


class EnvironmentGranularity(str, Enum):
    NATIONAL = "NATIONAL"
    REGION = "REGION"
    SUBZONE = "SUBZONE"


class WarningSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class DataAvailabilityCode(str, Enum):
    MISSING_SOURCE_DATA = "MISSING_SOURCE_DATA"
    VALID_ZERO = "VALID_ZERO"
    STALE_CACHE = "STALE_CACHE"
    PARTIAL_DATA = "PARTIAL_DATA"


@dataclass
class ValidationError:
    field: str
    message: str


@dataclass
class ValidationResult:
    isValid: bool
    errors: list[ValidationError]

    def addError(self, field: str, message: str) -> None: ...


@dataclass
class RetrievalResult(Generic[T]):
    data: T
    warnings: list[DataAvailabilityWarning]


@dataclass
class MapData:
    geojson: JSON
    scores: dict[str, float]
    center: Coordinates


@dataclass
class RouteData:
    geometry: str
    distanceKm: float
    durationMinutes: int
    mode: TransitMode


@dataclass
class RawResponse:
    statusCode: int
    body: JSON
    headers: dict[str, str]
    fetchedAt: datetime
