"""Dependency-free geometry helpers used for subzone spatial logic.

Shapely is not available in every development environment, so the backend uses
this small polygon implementation. The public surface mirrors the subset of
Shapely used by the application and can be replaced by Shapely without changing
the controls.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

try:
    from shapely.geometry import MultiPolygon as _ShapelyMultiPolygon
    from shapely.geometry import Point as _ShapelyPoint
    from shapely.geometry import Polygon as _ShapelyPolygon
    from shapely.ops import nearest_points as _nearest_points

    SHAPELY_AVAILABLE = True
except ImportError:  # pragma: no cover - fallback for minimal environments
    SHAPELY_AVAILABLE = False
    _ShapelyMultiPolygon = None  # type: ignore[assignment]
    _ShapelyPoint = None  # type: ignore[assignment]
    _ShapelyPolygon = None  # type: ignore[assignment]
    _nearest_points = None  # type: ignore[assignment]

EARTH_RADIUS_KM = 6371.0088


@dataclass(frozen=True)
class Coordinates:
    """WGS84 coordinate."""

    latitude: float
    longitude: float


def haversineKm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance between two WGS84 points in kilometres."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


def _ringContains(ring: Sequence[tuple[float, float]], lat: float, lon: float) -> bool:
    """Ray-casting point-in-polygon for a ring of (lat, lon) pairs."""
    inside = False
    count = len(ring)
    if count < 3:
        return False
    j = count - 1
    for i in range(count):
        yi, xi = ring[i]
        yj, xj = ring[j]
        intersects = ((xi > lon) != (xj > lon)) and (
            lat < (yj - yi) * (lon - xi) / ((xj - xi) or 1e-15) + yi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def _ringAreaSqm(ring: Sequence[tuple[float, float]]) -> float:
    """Approximate ring area using an equirectangular projection."""
    if len(ring) < 3:
        return 0.0
    lat0 = sum(p[0] for p in ring) / len(ring)
    m_per_deg_lat = 110_574.0
    m_per_deg_lon = 111_320.0 * math.cos(math.radians(lat0))
    area = 0.0
    j = len(ring) - 1
    for i in range(len(ring)):
        yi, xi = ring[i]
        yj, xj = ring[j]
        area += (xj * m_per_deg_lon) * (yi * m_per_deg_lat) - (
            xi * m_per_deg_lon
        ) * (yj * m_per_deg_lat)
        j = i
    return abs(area) / 2.0


def _ringCentroid(ring: Sequence[tuple[float, float]]) -> tuple[float, float]:
    """Approximate area-weighted centroid of a ring."""
    if not ring:
        return (0.0, 0.0)
    lat0 = sum(p[0] for p in ring) / len(ring)
    m_per_deg_lat = 110_574.0
    m_per_deg_lon = 111_320.0 * math.cos(math.radians(lat0))
    area = 0.0
    cx = 0.0
    cy = 0.0
    j = len(ring) - 1
    for i in range(len(ring)):
        yi, xi = ring[i]
        yj, xj = ring[j]
        x_i, y_i = xi * m_per_deg_lon, yi * m_per_deg_lat
        x_j, y_j = xj * m_per_deg_lon, yj * m_per_deg_lat
        cross = x_i * y_j - x_j * y_i
        area += cross
        cx += (x_i + x_j) * cross
        cy += (y_i + y_j) * cross
        j = i
    if abs(area) < 1e-9:
        return (
            sum(p[0] for p in ring) / len(ring),
            sum(p[1] for p in ring) / len(ring),
        )
    area *= 0.5
    return (cy / (6 * area) / m_per_deg_lat, cx / (6 * area) / m_per_deg_lon)


def _closestPointOnSegment(
    lat: float,
    lon: float,
    a: tuple[float, float],
    b: tuple[float, float],
) -> tuple[float, float]:
    """Return the closest point on segment a-b using a local projection."""
    lat0 = math.radians((lat + a[0] + b[0]) / 3.0)
    m_per_deg_lat = 110_574.0
    m_per_deg_lon = 111_320.0 * math.cos(lat0)
    px, py = lon * m_per_deg_lon, lat * m_per_deg_lat
    ax, ay = a[1] * m_per_deg_lon, a[0] * m_per_deg_lat
    bx, by = b[1] * m_per_deg_lon, b[0] * m_per_deg_lat
    dx, dy = bx - ax, by - ay
    denom = dx * dx + dy * dy
    if denom <= 1e-12:
        return a
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / denom))
    return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))


class GeoPolygon:
    """Lightweight polygon/multipolygon supporting the operations used by controls."""

    def __init__(self, parts: Iterable[tuple[list[tuple[float, float]], list[list[tuple[float, float]]]]]) -> None:
        self._parts = [(outer, holes) for outer, holes in parts if len(outer) >= 3]
        self._shapely = _buildShapely(self._parts)

    @classmethod
    def fromGeoJSON(cls, geometry: dict) -> "GeoPolygon":
        """Build a polygon from a GeoJSON Polygon or MultiPolygon geometry."""
        kind = geometry.get("type")
        if kind == "Polygon":
            return cls([_jsonPolygonToRings(geometry.get("coordinates", []))])
        if kind == "MultiPolygon":
            return cls([_jsonPolygonToRings(poly) for poly in geometry.get("coordinates", [])])
        raise ValueError(f"Unsupported GeoJSON geometry: {kind}")

    def contains(self, latitude: float, longitude: float) -> bool:
        """Return whether the point lies inside the polygon and outside holes."""
        if self._shapely is not None:
            return bool(self._shapely.contains(_ShapelyPoint(longitude, latitude)))
        for outer, holes in self._parts:
            if _ringContains(outer, latitude, longitude) and not any(
                _ringContains(hole, latitude, longitude) for hole in holes
            ):
                return True
        return False

    def areaSqm(self) -> float:
        """Return approximate area in square metres."""
        total = 0.0
        for outer, holes in self._parts:
            total += _ringAreaSqm(outer) - sum(_ringAreaSqm(hole) for hole in holes)
        return max(0.0, total)

    def centroid(self) -> tuple[float, float]:
        """Return an approximate area-weighted centroid as (lat, lon)."""
        if self._shapely is not None:
            point = self._shapely.centroid
            return (point.y, point.x)
        weighted_lat = 0.0
        weighted_lon = 0.0
        total_area = 0.0
        for outer, _ in self._parts:
            area = _ringAreaSqm(outer)
            lat, lon = _ringCentroid(outer)
            weighted_lat += lat * area
            weighted_lon += lon * area
            total_area += area
        if total_area <= 0:
            points = [p for outer, _ in self._parts for p in outer]
            if not points:
                return (0.0, 0.0)
            return (
                sum(p[0] for p in points) / len(points),
                sum(p[1] for p in points) / len(points),
            )
        return (weighted_lat / total_area, weighted_lon / total_area)

    def representativePoint(self) -> tuple[float, float]:
        """Return a point guaranteed to lie inside the polygon when possible."""
        if self._shapely is not None:
            point = self._shapely.representative_point()
            return (point.y, point.x)
        centroid = self.centroid()
        if self.contains(*centroid):
            return centroid
        min_lat, max_lat, min_lon, max_lon = self.bounds()
        for rows in range(1, 41):
            for cols in range(1, 41):
                lat = min_lat + (max_lat - min_lat) * rows / 41
                lon = min_lon + (max_lon - min_lon) * cols / 41
                if self.contains(lat, lon):
                    return (lat, lon)
        for outer, _ in self._parts:
            if outer:
                return outer[0]
        return centroid

    def bounds(self) -> tuple[float, float, float, float]:
        """Return (min_lat, max_lat, min_lon, max_lon)."""
        if self._shapely is not None:
            min_lon, min_lat, max_lon, max_lat = self._shapely.bounds
            return (min_lat, max_lat, min_lon, max_lon)
        points = [p for outer, _ in self._parts for p in outer]
        if not points:
            return (0.0, 0.0, 0.0, 0.0)
        lats = [p[0] for p in points]
        lons = [p[1] for p in points]
        return (min(lats), max(lats), min(lons), max(lons))

    def distanceToKm(self, latitude: float, longitude: float) -> float:
        """Return the shortest distance from a point to the polygon boundary."""
        if self._shapely is not None:
            if self.contains(latitude, longitude):
                return 0.0
            point = _ShapelyPoint(longitude, latitude)
            nearest = _nearest_points(self._shapely.boundary, point)[0]
            return haversineKm(latitude, longitude, nearest.y, nearest.x)
        best = math.inf
        for outer, holes in self._parts:
            for ring in [outer, *holes]:
                for i in range(len(ring)):
                    a = ring[i]
                    b = ring[(i + 1) % len(ring)]
                    closest = _closestPointOnSegment(latitude, longitude, a, b)
                    best = min(best, haversineKm(latitude, longitude, closest[0], closest[1]))
        return 0.0 if self.contains(latitude, longitude) else best

    def toGeoJSON(self) -> dict:
        """Return a GeoJSON Polygon or MultiPolygon geometry."""
        polygons = []
        for outer, holes in self._parts:
            polygons.append([_ringToGeoJSON(outer), *[_ringToGeoJSON(hole) for hole in holes]])
        if len(polygons) == 1:
            return {"type": "Polygon", "coordinates": polygons[0]}
        return {"type": "MultiPolygon", "coordinates": polygons}

    def __repr__(self) -> str:
        return f"GeoPolygon(parts={len(self._parts)}, areaSqm={self.areaSqm():.0f})"


def _buildShapely(parts: list[tuple[list[tuple[float, float]], list[list[tuple[float, float]]]]]):
    """Build a Shapely geometry when the optional dependency is available."""
    if not SHAPELY_AVAILABLE or not parts:
        return None
    polygons = []
    for outer, holes in parts:
        exterior = [(lon, lat) for lat, lon in outer]
        interiors = [[(lon, lat) for lat, lon in hole] for hole in holes]
        polygons.append(_ShapelyPolygon(exterior, interiors))
    if len(polygons) == 1:
        return polygons[0]
    return _ShapelyMultiPolygon(polygons)


def _jsonPolygonToRings(coordinates: Sequence) -> tuple[list[tuple[float, float]], list[list[tuple[float, float]]]]:
    rings: list[list[tuple[float, float]]] = []
    for ring in coordinates:
        rings.append([(float(lat), float(lon)) for lon, lat in ring])
    if not rings:
        return ([], [])
    return (rings[0], rings[1:])


def _ringToGeoJSON(ring: Sequence[tuple[float, float]]) -> list[list[float]]:
    points = [[float(lon), float(lat)] for lat, lon in ring]
    if points and points[0] != points[-1]:
        points.append(points[0])
    return points


Polygon = GeoPolygon
