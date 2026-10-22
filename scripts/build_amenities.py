"""Build the local amenity point snapshot from Singapore open data.

The generated ``backend/assets/data/amenities.json`` is consumed by
``AmenityRetrievalControl``. Counts are computed with buffer-distance density:
every amenity point within a fixed radius of a subzone's representative point
is counted. The radii are schools 1.0 km, MRT 800 m, parks 500 m, healthcare
2.0 km and shopping malls 1.0 km.

Sources
-------
- MOE General information of schools (data.gov.sg)
- NParks Parks and Nature Reserves (data.gov.sg)
- LTA MRT Station Exit (data.gov.sg)
- HPB Breast Screening Centre and MOH Vaccination Polyclinics (data.gov.sg)
- OneMap Themes: hospitals
- OneMap Search: shopping malls
- LTA Carpark Rates: supplemental major-mall names

Usage
-----
    python scripts/build_amenities.py

Run it from the ``revised-skeleton`` directory (or use ``make amenities``).
The script uses the OneMap credentials in ``.env`` to geocode school postal
codes and to query the mall/hospital POI layers.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.adapter.data_gov_sg_adapter import DataGovSgAdapter
from app.adapter.one_map_api_adapter import OneMapApiAdapter, OneMapApiError
from app.config import Settings
from app.core.geometry import GeoPolygon

try:  # Shapely is in requirements.txt, but keep a fallback for minimal setups.
    from shapely.geometry import shape as shapelyShape
except ImportError:  # pragma: no cover - requirements include Shapely
    shapelyShape = None

SCHOOL_DATASET_ID = "d_688b934f82c1059ed0a6993d2a829089"
PARKS_DATASET_ID = "d_77d7ec97be83d44f61b85454f844382f"
MRT_DATASET_ID = "d_b39d3a0871985372d7e1637193335da5"
POLYCLINIC_DATASET_IDS = (
    "d_0cdfbf7e277e8bfa1ef79fadf4b71b56",  # HPB Breast Screening Centre (polyclinic locations)
    "d_b22489c7dc4065b6e7e45f177fdb33be",  # MOH Vaccination_Polyclinics
)
HOSPITAL_THEME = "moh_hospitals"
MALL_SEARCH_QUERIES = ("mall", "shopping centre")
MALL_SUPPLEMENT_DATASET_ID = "d_9f6056bdb6b1dfba57f063593e4f34ae"  # LTA Carpark Rates
SUPPLEMENTAL_MALL_TOKENS = (
    "VIVOCITY",
    "ION ORCHARD",
    "NEX",
    "JEM",
    "WESTGATE",
    "IMM",
    "WISMA ATRIA",
    "HARBOURFRONT CENTRE",
    "SINGPOST CENTRE",
    "SINGAPORE POST CENTRE",
    "313@SOMERSET",
    "TAMPINES 1",
    "PARKWAY PARADE",
    "I12 KATONG",
    "KINEX",
    "DOWNTOWN EAST",
    "JEWEL CHANGI AIRPORT",
    "PAYA LEBAR QUARTER",
    "THE CENTREPOINT",
    "ORCHARD CENTRAL",
    "ORCHARDGATEWAY",
    "WHEELOCK PLACE",
    "SHAW HOUSE",
)
SUPPLEMENTAL_MALL_NAMES = (
    "Waterway Point",
    "Northpoint City",
    "Compass One",
    "Junction 8",
    "AMK Hub",
    "White Sands",
    "112 Katong",
    "Jewel Changi Airport",
    "Paya Lebar Quarter",
    "KINEX",
    "JEM",
)

CATEGORY_ORDER = (
    "Primary School",
    "Secondary School",
    "Polyclinic",
    "Hospital",
    "Park",
    "Shopping Mall",
    "MRT",
)

MALL_NAME_PATTERN = re.compile(
    r"\b(MALL|SHOPPING CENTRE|SHOPPING CENTER|PLAZA|JUNCTION|SQUARE|COMPLEX|"
    r"GALLERIA|VILLAGE|WALK|HUB|CITY|POINT|MART|EMPORIUM)\b"
)
MALL_EXCLUDE_PATTERN = re.compile(
    r"CAR MALL|FURNITURE MALL|FOOD COURT|FOOD CENTRE|CAR PARK|HOTEL|HOSPITAL|CLINIC|"
    r"SCHOOL|COMMUNITY|MARKET|HAWKER|OFFICE|TOWER|BUILDING|STATION|BUS|"
    r"INTERCHANGE|CONDOMINIUM|APARTMENT|WAREHOUSE|INDUSTRIAL|SCIENCE|MUSEUM|"
    r"GALLERY|MEMORIAL|TEMPLE|CHURCH|MOSQUE|INN|FURAMA|GRAND PARK|"
    r"HOLIDAY INN|ROYAL PLAZA ON SCOTTS|ASIA SQUARE|BURLINGTON SQUARE|"
    r"CAPITAL SQUARE|REPUBLIC PLAZA|UOB PLAZA|MERCHANT SQUARE"
)

DEFAULT_OUTPUT = BACKEND_ROOT / "assets" / "data" / "amenities.json"


class AmenitySnapshotBuilder:
    """Fetch, normalise and de-duplicate amenity points."""

    def __init__(
        self,
        dataGov: DataGovSgAdapter,
        oneMap: OneMapApiAdapter,
        *,
        verbose: bool = True,
    ) -> None:
        """Create a builder with the supplied adapters."""
        self.dataGov = dataGov
        self.oneMap = oneMap
        self.verbose = verbose
        self._items: dict[tuple[str, str], dict[str, Any]] = {}
        self._geocodeCache: dict[str, tuple[float, float] | None] = {}
        self._placeGeocodeCache: dict[str, tuple[float, float] | None] = {}
        self._skipped: Counter[str] = Counter()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def build(self) -> list[dict[str, Any]]:
        """Return the sorted amenity records."""
        self._addSchools()
        self._addParks()
        self._addMrtStations()
        self._addHospitals()
        self._addPolyclinics()
        self._addMalls()
        self._addSupplementalMalls()
        self._addNamedMalls()

        items = sorted(
            self._items.values(),
            key=lambda item: (
                CATEGORY_ORDER.index(item["category"])
                if item["category"] in CATEGORY_ORDER
                else len(CATEGORY_ORDER),
                item["name"],
            ),
        )
        return items

    # ------------------------------------------------------------------
    # Source-specific collectors
    # ------------------------------------------------------------------
    def _addSchools(self) -> None:
        payload = self._download(SCHOOL_DATASET_ID, "MOE school directory")
        rows = _rows(payload)
        self._log(f"Schools: {len(rows)} rows; geocoding postal codes with OneMap")
        for index, row in enumerate(rows, start=1):
            level = str(row.get("mainlevel_code") or "").upper()
            if "PRIMARY" in level or "P1" in level:
                category = "Primary School"
            elif "SECONDARY" in level or "S1" in level:
                category = "Secondary School"
            else:
                self._skipped["school_level"] += 1
                continue

            name = str(row.get("school_name") or "").strip()
            postal = _normalisePostal(row.get("postal_code"))
            if not name or not postal:
                self._skipped["school_missing_postal"] += 1
                continue

            coordinates = self._geocodePostal(postal)
            if coordinates is None:
                self._skipped["school_geocode"] += 1
                continue
            self._add(name, category, *coordinates)
            if self.verbose and index % 50 == 0:
                self._log(f"  geocoded {index}/{len(rows)} school rows")

    def _addParks(self) -> None:
        payload = self._download(PARKS_DATASET_ID, "NParks parks and nature reserves")
        features = _features(payload)
        self._log(f"Parks: {len(features)} polygon features")
        for feature in features:
            properties = feature.get("properties") or {}
            name = str(properties.get("NAME") or "").strip()
            if not name:
                self._skipped["park_missing_name"] += 1
                continue
            coordinates = _representativePoint(feature.get("geometry") or {})
            if coordinates is None:
                self._skipped["park_geometry"] += 1
                continue
            self._add(name, "Park", *coordinates)

    def _addMrtStations(self) -> None:
        payload = self._download(MRT_DATASET_ID, "LTA MRT station exits")
        features = _features(payload)
        self._log(f"MRT: {len(features)} exit features; grouping by station")
        stations: dict[str, list[tuple[float, float]]] = {}
        for feature in features:
            properties = feature.get("properties") or {}
            name = str(properties.get("STATION_NA") or "").strip()
            coordinates = _pointCoordinates(feature.get("geometry") or {})
            if not name or coordinates is None:
                self._skipped["mrt_feature"] += 1
                continue
            stations.setdefault(name, []).append(coordinates)

        for name, points in stations.items():
            latitude = sum(point[0] for point in points) / len(points)
            longitude = sum(point[1] for point in points) / len(points)
            self._add(name, "MRT", latitude, longitude)

    def _addHospitals(self) -> None:
        payload = self.oneMap.getThemeData(HOSPITAL_THEME)
        rows = payload.get("SrchResults") or []
        self._log(f"Hospitals: {len(rows)} OneMap theme rows")
        for row in rows:
            name = str(row.get("NAME") or "").strip()
            coordinates = _latLng(row.get("LatLng"))
            if not name or coordinates is None:
                self._skipped["hospital_row"] += 1
                continue
            self._add(name, "Hospital", *coordinates)

    def _addPolyclinics(self) -> None:
        for datasetId in POLYCLINIC_DATASET_IDS:
            payload = self._download(datasetId, f"polyclinic dataset {datasetId}")
            features = _features(payload)
            self._log(f"Polyclinics: {len(features)} features from {datasetId}")
            for feature in features:
                properties = feature.get("properties") or {}
                name = str(properties.get("NAME") or properties.get("name") or "").strip()
                if "POLYCLINIC" not in name.upper():
                    continue
                coordinates = _pointCoordinates(feature.get("geometry") or {})
                if coordinates is None:
                    self._skipped["polyclinic_geometry"] += 1
                    continue
                self._add(name, "Polyclinic", *coordinates)

    def _addMalls(self) -> None:
        for query in MALL_SEARCH_QUERIES:
            page = 1
            pages = 1
            while page <= pages:
                payload = self._searchPage(query, page)
                pages = int(payload.get("totalNumPages") or 0)
                for row in payload.get("results") or []:
                    name = str(row.get("BUILDING") or row.get("SEARCHVAL") or "").strip()
                    postal = str(row.get("POSTAL") or "").strip()
                    if not name or postal.upper() in {"", "NIL"}:
                        self._skipped["mall_no_postal"] += 1
                        continue
                    if not MALL_NAME_PATTERN.search(name.upper()):
                        continue
                    if MALL_EXCLUDE_PATTERN.search(name.upper()):
                        self._skipped["mall_excluded"] += 1
                        continue
                    coordinates = _titleCoordinates(row)
                    if coordinates is None:
                        self._skipped["mall_geometry"] += 1
                        continue
                    self._add(name, "Shopping Mall", *coordinates)
                page += 1
                time.sleep(0.05)
            self._log(f"Malls: finished OneMap query '{query}' ({pages} pages)")

    def _addSupplementalMalls(self) -> None:
        payload = self._download(
            MALL_SUPPLEMENT_DATASET_ID,
            "LTA carpark rates (major malls)",
        )
        rows = _rows(payload)
        self._log(f"Malls: {len(rows)} supplemental LTA rows")
        for row in rows:
            name = str(row.get("carpark") or "").strip()
            if not name:
                continue
            upper = name.upper()
            if not MALL_NAME_PATTERN.search(upper) and not any(
                token in upper for token in SUPPLEMENTAL_MALL_TOKENS
            ):
                continue
            if MALL_EXCLUDE_PATTERN.search(upper) and "IMM" not in upper:
                self._skipped["mall_supplement_excluded"] += 1
                continue
            coordinates = self._geocodePlace(name)
            if coordinates is None:
                self._skipped["mall_supplement_geocode"] += 1
                continue
            self._add(name, "Shopping Mall", *coordinates)

    def _addNamedMalls(self) -> None:
        """Geocode major malls whose names do not match the LTA list."""
        self._log(f"Malls: {len(SUPPLEMENTAL_MALL_NAMES)} named major malls")
        for name in SUPPLEMENTAL_MALL_NAMES:
            coordinates = self._geocodePlace(name)
            if coordinates is None:
                self._skipped["mall_named_geocode"] += 1
                continue
            self._add(name, "Shopping Mall", *coordinates)

    # ------------------------------------------------------------------
    # Network / parsing helpers
    # ------------------------------------------------------------------
    def _download(self, datasetId: str, label: str) -> dict[str, Any]:
        self._log(f"Downloading {label} ({datasetId})")
        for attempt in range(4):
            try:
                payload = self.dataGov.fetchDataset(datasetId).body
                time.sleep(6.0)
                return payload
            except Exception as exc:
                if "429" not in str(exc) or attempt == 3:
                    raise
                wait = 12.0 * (attempt + 1)
                self._log(f"  data.gov.sg rate limit; sleeping {wait:.0f}s")
                time.sleep(wait)
        raise RuntimeError("data.gov.sg download retry loop exhausted")

    def _searchPage(self, query: str, page: int) -> dict[str, Any]:
        for attempt in range(3):
            try:
                return self.oneMap.searchPlaces(query, page)
            except OneMapApiError as exc:
                if exc.statusCode == 429 and attempt < 2:
                    wait = 2.0 * (attempt + 1)
                    self._log(f"  OneMap rate limit; sleeping {wait:.1f}s")
                    time.sleep(wait)
                    continue
                raise
        raise RuntimeError("OneMap search retry loop exhausted")

    def _geocodePostal(self, postal: str) -> tuple[float, float] | None:
        if postal in self._geocodeCache:
            return self._geocodeCache[postal]
        for attempt in range(3):
            try:
                matches = self.oneMap.searchAddress(postal)
                break
            except OneMapApiError as exc:
                if exc.statusCode == 429 and attempt < 2:
                    wait = 2.0 * (attempt + 1)
                    self._log(f"  OneMap rate limit while geocoding {postal}; sleeping {wait:.1f}s")
                    time.sleep(wait)
                    continue
                self._log(f"  Geocoding failed for postal code {postal}: {exc}")
                self._geocodeCache[postal] = None
                return None
        else:  # pragma: no cover - defensive
            self._geocodeCache[postal] = None
            return None

        exact = next(
            (
                match
                for match in matches
                if _normalisePostal(match.postalCode) == postal
            ),
            None,
        )
        match = exact or (matches[0] if matches else None)
        if match is None:
            self._geocodeCache[postal] = None
            return None

        coordinates = (match.coordinates.latitude, match.coordinates.longitude)
        self._geocodeCache[postal] = coordinates
        time.sleep(0.08)
        return coordinates

    def _geocodePlace(self, name: str) -> tuple[float, float] | None:
        key = _normaliseName(name)
        if key in self._placeGeocodeCache:
            return self._placeGeocodeCache[key]
        for attempt in range(3):
            try:
                matches = self.oneMap.searchAddress(name)
                break
            except OneMapApiError as exc:
                if exc.statusCode == 429 and attempt < 2:
                    wait = 2.0 * (attempt + 1)
                    self._log(f"  OneMap rate limit while geocoding {name}; sleeping {wait:.1f}s")
                    time.sleep(wait)
                    continue
                self._log(f"  Geocoding failed for {name}: {exc}")
                self._placeGeocodeCache[key] = None
                return None
        else:  # pragma: no cover - defensive
            self._placeGeocodeCache[key] = None
            return None

        if not matches:
            self._placeGeocodeCache[key] = None
            return None
        match = matches[0]
        coordinates = (match.coordinates.latitude, match.coordinates.longitude)
        self._placeGeocodeCache[key] = coordinates
        time.sleep(0.08)
        return coordinates

    def _add(self, name: str, category: str, latitude: float, longitude: float) -> None:
        key = (category, _normaliseName(name))
        if key in self._items:
            return
        self._items[key] = {
            "name": name,
            "category": category,
            "latitude": round(float(latitude), 6),
            "longitude": round(float(longitude), 6),
        }

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message, flush=True)


def _rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    rows = payload.get("rows") or payload.get("items") or payload.get("amenities") or []
    return [row for row in rows if isinstance(row, dict)]


def _features(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and payload.get("type") == "FeatureCollection":
        return [
            feature
            for feature in payload.get("features", [])
            if isinstance(feature, dict)
        ]
    return []


def _pointCoordinates(geometry: dict[str, Any]) -> tuple[float, float] | None:
    if geometry.get("type") != "Point":
        return None
    coordinates = geometry.get("coordinates") or []
    if len(coordinates) < 2:
        return None
    try:
        return (float(coordinates[1]), float(coordinates[0]))
    except (TypeError, ValueError):
        return None


def _representativePoint(geometry: dict[str, Any]) -> tuple[float, float] | None:
    if shapelyShape is not None:
        try:
            shape = shapelyShape(geometry)
            if not shape.is_valid:
                shape = shape.buffer(0)
            point = shape.representative_point()
            return (float(point.y), float(point.x))
        except Exception:
            pass
    try:
        return GeoPolygon.fromGeoJSON(geometry).representativePoint()
    except (KeyError, TypeError, ValueError):
        return None


def _latLng(value: Any) -> tuple[float, float] | None:
    if not isinstance(value, str) or "," not in value:
        return None
    latitude, longitude = value.split(",", 1)
    try:
        return (float(latitude), float(longitude))
    except ValueError:
        return None


def _titleCoordinates(row: dict[str, Any]) -> tuple[float, float] | None:
    try:
        return (float(row["LATITUDE"]), float(row["LONGITUDE"]))
    except (KeyError, TypeError, ValueError):
        return None


def _normalisePostal(value: Any) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) == 5:
        digits = f"0{digits}"
    if len(digits) == 6:
        return digits
    return ""


def _normaliseName(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().upper())


def _buildAdapters(settings: Settings) -> tuple[DataGovSgAdapter, OneMapApiAdapter]:
    dataGov = DataGovSgAdapter(
        apiEndpoint=settings.DATA_GOV_SG_BASE_URL,
        apiKey=settings.DATA_GOV_SG_API_KEY,
        fallbackDir=BACKEND_ROOT / "assets" / "data",
    )
    oneMap = OneMapApiAdapter(
        settings.ONEMAP_BASE_URL,
        settings.ONEMAP_EMAIL or "",
        settings.ONEMAP_PASSWORD or "",
    )
    return dataGov, oneMap


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")
    args = parser.parse_args(argv)

    settings = Settings.fromEnv()
    dataGov, oneMap = _buildAdapters(settings)
    builder = AmenitySnapshotBuilder(dataGov, oneMap, verbose=not args.quiet)
    items = builder.build()

    counts = Counter(item["category"] for item in items)
    payload = {
        "metadata": {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "method": "buffer_distance_density",
            "anchor": "subzone representative point",
            "radiiKm": {
                "schools": 1.0,
                "mrt": 0.8,
                "parks": 0.5,
                "healthcare": 2.0,
                "malls": 1.0,
            },
            "sources": {
                "schools": "MOE General information of schools (data.gov.sg)",
                "parks": "NParks Parks and Nature Reserves (data.gov.sg)",
                "mrt": "LTA MRT Station Exit (data.gov.sg)",
                "polyclinics": "HPB Breast Screening Centre and MOH Vaccination Polyclinics (data.gov.sg)",
                "hospitals": "OneMap Hospitals theme (MOH)",
                "malls": "OneMap Search (mall / shopping centre) + LTA Carpark Rates major-mall names + named major malls",
            },
            "counts": dict(sorted(counts.items())),
        },
        "items": items,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {len(items)} amenities to {args.output}")
    for category in CATEGORY_ORDER:
        print(f"  {category}: {counts.get(category, 0)}")
    if builder._skipped:
        print("Skipped rows: " + ", ".join(f"{key}={value}" for key, value in sorted(builder._skipped.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
