"""Shared entity types and value objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Generic, TypeAlias, TypeVar

if TYPE_CHECKING:
    from app.entity.data_availability_warning import DataAvailabilityWarning
    from app.entity.enums import TransitMode

JSON: TypeAlias = dict[str, Any]
T = TypeVar("T")


@dataclass
class Coordinates:
    """Stereotype: Entity. WGS84 latitude/longitude pair."""

    latitude: float
    longitude: float

    def toOneMapString(self) -> str:
        """Return the `lat,lng` representation expected by OneMap."""
        return f"{self.latitude},{self.longitude}"

    def toGeoJSON(self) -> tuple[float, float]:
        """Return the `(lng, lat)` representation expected by GeoJSON."""
        return (self.longitude, self.latitude)


@dataclass
class ValidationError:
    """Stereotype: Entity. One invalid profile field."""

    field: str
    message: str


@dataclass
class ValidationResult:
    """Stereotype: Entity. Outcome of profile validation."""

    isValid: bool
    errors: list[ValidationError]

    def addError(self, field: str, message: str) -> None:
        """Append a field-level validation error and mark the result invalid."""
        self.errors.append(ValidationError(field, message))
        self.isValid = False


@dataclass
class RetrievalResult(Generic[T]):
    """Stereotype: Entity. Request-scoped data plus warnings."""

    data: T
    warnings: list[DataAvailabilityWarning]


@dataclass
class MapData:
    """Stereotype: Entity. Serialisable map payload for Leaflet."""

    geojson: JSON
    scores: dict[str, float]
    center: Coordinates


@dataclass
class RouteData:
    """Stereotype: Entity. Route geometry and summary."""

    geometry: str
    distanceKm: float
    durationMinutes: int
    mode: TransitMode


@dataclass
class RawResponse:
    """Stereotype: Entity. Raw external API response."""

    statusCode: int
    body: JSON
    headers: dict[str, str]
    fetchedAt: datetime
