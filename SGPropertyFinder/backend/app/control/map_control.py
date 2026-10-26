"""Map payload and commute-overlay control."""

from __future__ import annotations

import math
from datetime import datetime
from typing import TYPE_CHECKING

from app.core.polyline import mergeEncodedPolylines
from app.entity.types import Coordinates, MapData, RouteData

if TYPE_CHECKING:
    from app.adapter.one_map_api_adapter import OneMapApiAdapter
    from app.container.subzone_registry import SubzoneRegistry
    from app.control.commute_control import CommuteControl
    from app.core.geometry import Polygon
    from app.entity.enums import TransitMode


class MapControl:
    """Stereotype: Control. Prepares map payloads and commute overlays."""

    def __init__(
        self,
        subzoneRegistry: SubzoneRegistry,
        oneMapAdapter: OneMapApiAdapter,
        commuteControl: CommuteControl,
    ) -> None:
        """Store map dependencies."""
        self.subzoneRegistry = subzoneRegistry
        self.oneMapAdapter = oneMapAdapter
        self.commuteControl = commuteControl

    def generateMapData(self, scores: dict[str, float] | None = None) -> MapData:
        """Return Leaflet-ready GeoJSON, scores and a map center."""
        subzones = self.subzoneRegistry.getAllSubzones()
        if subzones:
            center = Coordinates(
                sum(s.centroid.latitude for s in subzones) / len(subzones),
                sum(s.centroid.longitude for s in subzones) / len(subzones),
            )
        else:
            center = Coordinates(1.3521, 103.8198)
        return MapData(
            geojson=self.subzoneRegistry.toFeatureCollection(scores),
            scores=dict(scores or {}),
            center=center,
        )

    def fetchSubzoneBoundary(self, subzoneCode: str) -> Polygon:
        """Return the polygon for a subzone, raising when unknown."""
        return self.subzoneRegistry.getSubzone(subzoneCode).boundaryPolygon

    def getCommuteOverlay(
        self,
        origin: Coordinates,
        destination: Coordinates,
        mode: TransitMode,
        departureTime: datetime | None = None,
    ) -> RouteData:
        """Return route geometry and summary from OneMap."""
        payload = self.oneMapAdapter.getRoutingData(origin, destination, mode, departureTime)
        summary = payload.get("route_summary") or {}
        if summary:
            return RouteData(
                geometry=str(payload.get("route_geometry") or ""),
                distanceKm=round(float(summary.get("total_distance", 0)) / 1000, 3),
                durationMinutes=max(1, math.ceil(float(summary.get("total_time", 0)) / 60)),
                mode=mode,
            )
        itineraries = payload.get("plan", {}).get("itineraries", [])
        if itineraries:
            legs = itineraries[0].get("legs", [])
            distance = sum(float(leg.get("distance", 0)) for leg in legs)
            geometry = mergeEncodedPolylines(
                leg.get("legGeometry", {}).get("points") for leg in legs
            )
            return RouteData(
                geometry=geometry,
                distanceKm=round(distance / 1000, 3),
                durationMinutes=max(1, math.ceil(float(itineraries[0].get("duration", 0)) / 60)),
                mode=mode,
            )
        raise ValueError("OneMap route response had no summary or itineraries")
