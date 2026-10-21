"""Types module."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Generic, TypeAlias, TypeVar
if TYPE_CHECKING:
    from app.entity.data_availability_warning import DataAvailabilityWarning
    from app.entity.enums import TransitMode
JSON: TypeAlias = dict[str, Any]
T = TypeVar('T')

@dataclass
class Coordinates:
    """Stereotype: Entity. Entity value object representing a WGS84 latitude/longitude pair."""
    latitude: float
    longitude: float

    def toOneMapString(self) -> str:
        """Return the `lat,lng` string expected by OneMap.

        Args:
            None.

        Returns:
            str.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def toGeoJSON(self) -> tuple[float, float]:
        """Return the `(lng, lat)` pair expected by GeoJSON.

        Args:
            None.

        Returns:
            tuple[float, float].

        Failure handling:
            Not applicable at the skeleton level."""
        ...

@dataclass
class ValidationError:
    """Stereotype: Entity. Entity value object describing one invalid profile field."""
    field: str
    message: str

@dataclass
class ValidationResult:
    """Stereotype: Entity. Entity value object containing the outcome of profile validation."""
    isValid: bool
    errors: list[ValidationError]

    def addError(self, field: str, message: str) -> None:
        """Append a field-level validation error.

        Args:
            field: str
            message: str

        Returns:
            None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

@dataclass
class RetrievalResult(Generic[T]):
    """Stereotype: Entity. Entity value object carrying request-scoped retrieved data and warnings."""
    data: T
    warnings: list[DataAvailabilityWarning]

@dataclass
class MapData:
    """Stereotype: Entity. Entity value object carrying Leaflet-ready GeoJSON, scores and map center."""
    geojson: JSON
    scores: dict[str, float]
    center: Coordinates

@dataclass
class RouteData:
    """Stereotype: Entity. Entity value object carrying route geometry and summary values."""
    geometry: str
    distanceKm: float
    durationMinutes: int
    mode: TransitMode

@dataclass
class RawResponse:
    """Stereotype: Entity. Entity value object wrapping an unparsed external API response."""
    statusCode: int
    body: JSON
    headers: dict[str, str]
    fetchedAt: datetime
