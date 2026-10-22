"""Amenity retrieval and per-subzone counts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING

from app.control.retrieval_control import RetrievalControl
from app.core.geometry import haversineKm
from app.entity.amenity_info import AmenityInfo
from app.entity.enums import DataAvailabilityCode
from app.entity.subzone_indicators import SubzoneIndicators
from app.entity.types import Coordinates, RawResponse, RetrievalResult

if TYPE_CHECKING:
    from app.adapter.data_gov_sg_adapter import DataGovSgAdapter
    from app.container.subzone_registry import SubzoneRegistry
    from app.control.data_availability_notifier import DataAvailabilityNotifier

DISPLAY_RADIUS_KM = 2.0
SCHOOL_RADIUS_KM = 1.0
MRT_RADIUS_KM = 0.8
PARK_RADIUS_KM = 0.5
HEALTHCARE_RADIUS_KM = 2.0
MALL_RADIUS_KM = 1.0


class AmenityRetrievalControl(RetrievalControl):
    """Stereotype: Control. Retrieves amenities and computes proximity indicators.

    Counts use buffer-distance density: every amenity point within the fixed
    radius of the subzone's representative point (the registry stores this as
    ``centroid``) is counted. The radii are schools 1.0 km, MRT 800 m, parks
    500 m, healthcare 2.0 km and shopping malls 1.0 km.
    """

    def __init__(
        self,
        dataGovAdapter: DataGovSgAdapter,
        notifier: DataAvailabilityNotifier,
        amenitiesPath: Path | str | None = None,
        subzoneRegistry: SubzoneRegistry | None = None,
    ) -> None:
        """Create the amenity control.

        Args:
            dataGovAdapter: Data.gov.sg adapter.
            notifier: Stateless warning factory.
            amenitiesPath: Optional local JSON/GeoJSON amenity file.
            subzoneRegistry: Registry used to resolve subzone anchors.
        """
        super().__init__(dataGovAdapter, notifier)
        self.amenitiesPath = Path(amenitiesPath) if amenitiesPath else None
        self.subzoneRegistry = subzoneRegistry
        self._amenitiesCache: list[dict[str, Any]] | None = None
        self._amenitiesError = False

    def fetchData(self, resourceId: str) -> RawResponse:
        """Fetch the amenity payload."""
        if self.amenitiesPath and self.amenitiesPath.exists():
            payload = json.loads(self.amenitiesPath.read_text(encoding="utf-8"))
            return RawResponse(
                statusCode=200,
                body=payload if isinstance(payload, dict) else {"items": payload},
                headers={"Content-Type": "application/json"},
                fetchedAt=datetime.now(timezone.utc),
            )
        return self.dataGovAdapter.fetchDataset(resourceId)

    def parseResponse(self, data: RawResponse) -> list[dict[str, Any]]:
        """Normalise simple and GeoJSON amenity payloads."""
        body = data.body
        if isinstance(body, dict) and body.get("type") == "FeatureCollection":
            items = []
            for feature in body.get("features", []):
                geometry = feature.get("geometry") or {}
                coords = geometry.get("coordinates") or []
                if geometry.get("type") != "Point" or len(coords) < 2:
                    continue
                props = feature.get("properties") or {}
                items.append(
                    {
                        **props,
                        "longitude": coords[0],
                        "latitude": coords[1],
                    }
                )
            return items
        if isinstance(body, dict):
            items = body.get("items", body.get("amenities", []))
        else:
            items = body
        return [dict(item) for item in items if isinstance(item, dict)]

    def _amenities(self) -> list[dict[str, Any]]:
        if self._amenitiesCache is None:
            try:
                raw = self.fetchData("amenities")
                self._amenitiesCache = self.parseResponse(raw)
                self._amenitiesError = False
            except Exception:
                self._amenitiesCache = []
                self._amenitiesError = True
        return self._amenitiesCache

    def retrieveAmenityInfo(self, subzoneCode: str) -> RetrievalResult[list[AmenityInfo]]:
        """Return amenities within the display radius of a subzone."""
        warnings = []
        if self.subzoneRegistry is None:
            warnings.append(
                self.handleMissingData("AMENITIES", subzoneCode, DataAvailabilityCode.MISSING_SOURCE_DATA)
            )
            return RetrievalResult([], warnings)
        try:
            subzone = self.subzoneRegistry.getSubzone(subzoneCode)
        except KeyError:
            warnings.append(
                self.handleMissingData("AMENITIES", subzoneCode, DataAvailabilityCode.MISSING_SOURCE_DATA)
            )
            return RetrievalResult([], warnings)

        amenities = []
        source_rows = self._amenities()
        if self._amenitiesError:
            warnings.append(
                self.handleMissingData(
                    "AMENITIES",
                    subzoneCode,
                    DataAvailabilityCode.MISSING_SOURCE_DATA,
                    message="Amenity dataset unavailable",
                )
            )
        for item in source_rows:
            category = _category(item)
            lat = _optionalFloat(item.get("latitude", item.get("lat")))
            lon = _optionalFloat(item.get("longitude", item.get("lng", item.get("lon"))))
            if not category or lat is None or lon is None:
                continue
            distance = haversineKm(subzone.centroid.latitude, subzone.centroid.longitude, lat, lon)
            if distance <= DISPLAY_RADIUS_KM:
                amenities.append(
                    AmenityInfo(
                        amenityName=str(item.get("name") or item.get("amenityName") or "Unnamed"),
                        category=category,
                        location=Coordinates(lat, lon),
                        distanceKm=round(distance, 3),
                    )
                )
        amenities.sort(key=lambda item: item.distanceKm or 0.0)
        return RetrievalResult(amenities, warnings)

    def getAllAmenities(self) -> RetrievalResult[list[dict[str, Any]]]:
        """Return every amenity point for the map overlay layer."""
        warnings = []
        source_rows = self._amenities()
        if self._amenitiesError:
            warnings.append(
                self.handleMissingData(
                    "AMENITIES",
                    None,
                    DataAvailabilityCode.MISSING_SOURCE_DATA,
                    message="Amenity dataset unavailable",
                )
            )
        items: list[dict[str, Any]] = []
        for item in source_rows:
            category = str(
                item.get("category") or item.get("type") or item.get("CLASS") or ""
            ).strip()
            if not category:
                category = _category(item)
            latitude = _optionalFloat(item.get("latitude", item.get("lat")))
            longitude = _optionalFloat(item.get("longitude", item.get("lng", item.get("lon"))))
            if not category or latitude is None or longitude is None:
                continue
            items.append(
                {
                    "name": str(
                        item.get("name") or item.get("amenityName") or "Unnamed"
                    ),
                    "category": category,
                    "latitude": latitude,
                    "longitude": longitude,
                }
            )
        items.sort(key=lambda item: (item["category"], item["name"]))
        return RetrievalResult(items, warnings)

    def retrieveIndicators(self, subzoneCode: str) -> RetrievalResult[SubzoneIndicators]:
        """Compute school, healthcare, park, mall and MRT indicators."""
        warnings = []
        if self.subzoneRegistry is None:
            warnings.append(
                self.handleMissingData("AMENITIES", subzoneCode, DataAvailabilityCode.MISSING_SOURCE_DATA)
            )
            return RetrievalResult(SubzoneIndicators(), warnings)
        try:
            subzone = self.subzoneRegistry.getSubzone(subzoneCode)
        except KeyError:
            warnings.append(
                self.handleMissingData("AMENITIES", subzoneCode, DataAvailabilityCode.MISSING_SOURCE_DATA)
            )
            return RetrievalResult(SubzoneIndicators(), warnings)

        rows = []
        source_rows = self._amenities()
        if self._amenitiesError:
            warnings.append(
                self.handleMissingData(
                    "AMENITIES",
                    subzoneCode,
                    DataAvailabilityCode.MISSING_SOURCE_DATA,
                    message="Amenity dataset unavailable",
                )
            )
        for item in source_rows:
            category = _category(item)
            lat = _optionalFloat(item.get("latitude", item.get("lat")))
            lon = _optionalFloat(item.get("longitude", item.get("lng", item.get("lon"))))
            if not category or lat is None or lon is None:
                continue
            distance = haversineKm(subzone.centroid.latitude, subzone.centroid.longitude, lat, lon)
            rows.append((category, distance, item))

        indicators = SubzoneIndicators(
            nearestParkM=_nearestM(rows, "park"),
            parkCount500m=_count(rows, "park", PARK_RADIUS_KM),
            nearestSchoolM=_nearestM(rows, "school"),
            primarySchoolCount1km=_count(rows, "school", SCHOOL_RADIUS_KM, subtype="primary"),
            secondarySchoolCount1km=_count(rows, "school", SCHOOL_RADIUS_KM, subtype="secondary"),
            nearestPolyclinicM=_nearestM(rows, "polyclinic"),
            polyclinicCount2km=_count(rows, "polyclinic", HEALTHCARE_RADIUS_KM),
            nearestHospitalM=_nearestM(rows, "hospital"),
            hospitalCount2km=_count(rows, "hospital", HEALTHCARE_RADIUS_KM),
            nearestMallM=_nearestM(rows, "mall"),
            mallCount1km=_count(rows, "mall", MALL_RADIUS_KM),
            nearestMrtM=_nearestM(rows, "mrt"),
            mrtStationCount800m=_count(rows, "mrt", MRT_RADIUS_KM),
            amenityDataAvailable=not self._amenitiesError,
        )
        return RetrievalResult(indicators, warnings)


def _category(item: dict[str, Any]) -> str:
    raw = str(item.get("category") or item.get("type") or item.get("CLASS") or "").strip().lower()
    if "primary" in raw or "secondary" in raw or raw in {"school", "schools"}:
        return "school"
    if "polyclinic" in raw:
        return "polyclinic"
    if "hospital" in raw:
        return "hospital"
    if "park" in raw:
        return "park"
    if "mall" in raw or "shopping" in raw:
        return "mall"
    if raw in {"mrt", "lrt", "station"}:
        return "mrt"
    return raw


def _subtype(item: dict[str, Any]) -> str:
    text = " ".join(str(item.get(key, "")) for key in ("subtype", "level", "name", "category")).lower()
    if "primary" in text:
        return "primary"
    if "secondary" in text:
        return "secondary"
    return ""


def _count(rows: list[tuple[str, float, dict[str, Any]]], category: str, radius_km: float, subtype: str | None = None) -> int:
    total = 0
    for row_category, distance, item in rows:
        if row_category != category or distance > radius_km:
            continue
        if subtype and _subtype(item) != subtype:
            continue
        total += 1
    return total


def _nearestM(rows: list[tuple[str, float, dict[str, Any]]], category: str) -> float | None:
    distances = [distance for row_category, distance, _ in rows if row_category == category]
    return round(min(distances) * 1000, 1) if distances else None


def _optionalFloat(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
