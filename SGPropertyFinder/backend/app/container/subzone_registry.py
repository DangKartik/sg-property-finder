"""In-memory subzone registry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TYPE_CHECKING

from app.core.geometry import GeoPolygon
from app.entity.subzone import Subzone
from app.entity.subzone_indicators import SubzoneIndicators
from app.entity.types import Coordinates

if TYPE_CHECKING:
    from app.container.town_mapping import TownMapping


class SubzoneRegistry:
    """Stereotype: Container. Holds the in-memory subzone registry."""

    subzones: dict[str, Subzone]

    def __init__(self, subzones: dict[str, Subzone] | None = None) -> None:
        """Create an empty or pre-populated registry."""
        self.subzones = dict(subzones or {})

    def registerSubzone(self, subzone: Subzone) -> None:
        """Register or replace a subzone."""
        self.subzones[subzone.getSubzoneCode()] = subzone

    def getSubzone(self, subzoneCode: str) -> Subzone:
        """Return a subzone by code.

        Raises:
            KeyError: If the code is not registered.
        """
        try:
            return self.subzones[subzoneCode]
        except KeyError as exc:
            raise KeyError(f"Unknown subzone: {subzoneCode}") from exc

    def getAllSubzones(self) -> list[Subzone]:
        """Return all registered subzones."""
        return list(self.subzones.values())

    def findSubzoneForCoordinates(self, latitude: float, longitude: float) -> Subzone | None:
        """Return the first subzone containing the point, if any."""
        for subzone in self.subzones.values():
            if subzone.boundaryPolygon.contains(latitude, longitude):
                return subzone
        return None

    @classmethod
    def fromGeoJson(
        cls,
        path: Path | str,
        townMapping: TownMapping | None = None,
    ) -> "SubzoneRegistry":
        """Load subzones from a URA-style GeoJSON FeatureCollection.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the payload is not a FeatureCollection.
        """
        source = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.fromGeoJsonPayload(source, townMapping)

    @classmethod
    def fromGeoJsonPayload(
        cls,
        source: dict[str, Any],
        townMapping: TownMapping | None = None,
    ) -> "SubzoneRegistry":
        """Load subzones from an in-memory GeoJSON FeatureCollection."""
        if source.get("type") != "FeatureCollection":
            raise ValueError("Subzone data must be a GeoJSON FeatureCollection")

        registry = cls()
        for feature in source.get("features", []):
            props: dict[str, Any] = feature.get("properties") or {}
            code = str(props.get("SUBZONE_C") or props.get("subzoneCode") or props.get("SUBZONE_NO") or "").strip()
            name = str(props.get("SUBZONE_N") or props.get("subzoneName") or props.get("name") or code).strip()
            planning_area = str(props.get("PLN_AREA_N") or props.get("planningAreaName") or "").strip()
            region = str(props.get("REGION_N") or props.get("regionName") or "UNKNOWN").strip()
            if not code:
                continue

            town = str(props.get("townName") or props.get("TOWN") or "").strip().upper()
            if not town and townMapping is not None:
                town = townMapping.resolveTown(planning_area) or ""
            if not town:
                town = planning_area.upper() or "UNKNOWN"

            polygon = GeoPolygon.fromGeoJSON(feature.get("geometry") or {})
            lat, lon = polygon.representativePoint()
            registry.registerSubzone(
                Subzone(
                    subzoneCode=code,
                    subzoneName=name,
                    planningAreaName=planning_area,
                    townName=town,
                    boundaryPolygon=polygon,
                    regionName=region,
                    centroid=Coordinates(lat, lon),
                    indicators=SubzoneIndicators(),
                )
            )
        return registry

    def toFeatureCollection(self, scores: dict[str, float] | None = None) -> dict[str, Any]:
        """Serialize the registry as a GeoJSON FeatureCollection."""
        score_map = scores or {}
        features = []
        for subzone in self.subzones.values():
            features.append(
                {
                    "type": "Feature",
                    "geometry": subzone.boundaryPolygon.toGeoJSON(),
                    "properties": {
                        "subzoneCode": subzone.subzoneCode,
                        "subzoneName": subzone.subzoneName,
                        "planningAreaName": subzone.planningAreaName,
                        "townName": subzone.townName,
                        "regionName": subzone.regionName,
                        "score": score_map.get(subzone.subzoneCode),
                        "dataAvailable": subzone.dataAvailable,
                    },
                }
            )
        return {"type": "FeatureCollection", "features": features}
