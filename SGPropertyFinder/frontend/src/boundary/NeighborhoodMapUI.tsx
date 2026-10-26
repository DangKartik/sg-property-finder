import { useMemo, useState } from "react";
import type { Feature, GeoJsonObject } from "geojson";
import type { Layer, PathOptions } from "leaflet";
import {
  CircleMarker,
  GeoJSON,
  MapContainer,
  Polyline,
  TileLayer,
  Tooltip,
} from "react-leaflet";
import type {
  AmenityPointDTO,
  CoordinatesDTO,
  MapDataDTO,
  RouteDataDTO,
} from "../types/dto";
import { decodePolyline } from "../utils/polyline";
import { scoreColor } from "../utils/format";
import {
  ALL_AMENITY_GROUP_IDS,
  AMENITY_GROUPS,
  amenityColor,
  filterAmenities,
} from "../utils/amenities";

export interface NeighborhoodMapUIProps {
  mapData: MapDataDTO | null;
  scores: Record<string, number>;
  selectedSubzoneId: string | null;
  highlightedSubzoneIds?: string[];
  amenities?: AmenityPointDTO[];
  route: RouteDataDTO | null;
  routeOrigin: CoordinatesDTO | null;
  routeDestination: CoordinatesDTO | null;
  onSelect: (subzoneId: string) => void;
  onRefresh?: () => void;
  refreshing?: boolean;
}

const SINGAPORE_CENTER: [number, number] = [1.3521, 103.8198];

/** OneMap-backed map with a subzone choropleth, route overlay and selected-subzone amenities. */
export function NeighborhoodMapUI({
  mapData,
  scores,
  selectedSubzoneId,
  highlightedSubzoneIds = [],
  amenities = [],
  route,
  routeOrigin,
  routeDestination,
  onSelect,
  onRefresh,
  refreshing = false,
}: NeighborhoodMapUIProps) {
  const [visibleGroups, setVisibleGroups] = useState<string[]>(
    ALL_AMENITY_GROUP_IDS,
  );
  const visibleAmenities = useMemo(
    () => filterAmenities(amenities, true, visibleGroups),
    [amenities, visibleGroups],
  );

  function toggleGroup(groupId: string) {
    setVisibleGroups((current) =>
      current.includes(groupId)
        ? current.filter((id) => id !== groupId)
        : [...current, groupId],
    );
  }

  const center: [number, number] = mapData
    ? [mapData.center.latitude, mapData.center.longitude]
    : SINGAPORE_CENTER;
  const routePositions =
    decodePolyline(route?.geometry).length > 0
      ? decodePolyline(route?.geometry)
      : routeOrigin && routeDestination
        ? [
            [routeOrigin.latitude, routeOrigin.longitude] as [number, number],
            [routeDestination.latitude, routeDestination.longitude] as [number, number],
          ]
        : [];
  const mapStyle = useMemo(
    () => (feature: Feature | undefined) =>
      styleFeature(feature, scores, selectedSubzoneId, highlightedSubzoneIds),
    [scores, selectedSubzoneId, highlightedSubzoneIds],
  );

  return (
    <section className="map-panel" aria-label="Neighbourhood suitability map">
      <MapContainer
        center={center}
        zoom={11}
        minZoom={11}
        scrollWheelZoom
        className="leaflet-container"
      >
        <TileLayer
          attribution='Map data &copy; <a href="https://www.onemap.gov.sg/">OneMap Singapore</a>'
          url="https://www.onemap.gov.sg/maps/tiles/Default/{z}/{x}/{y}.png"
          maxZoom={19}
        />
        {mapData && (
          <GeoJSON
            data={mapData.geojson as GeoJsonObject}
            style={mapStyle}
            onEachFeature={(feature, layer) => bindFeature(feature, layer, onSelect)}
          />
        )}
        {visibleAmenities.map((amenity, index) => {
          const color = amenityColor(amenity.category);
          return (
            <CircleMarker
              key={`${amenity.category}-${amenity.name}-${index}`}
              center={[amenity.latitude, amenity.longitude]}
              radius={3.2}
              pathOptions={{
                color,
                fillColor: color,
                fillOpacity: 0.78,
                weight: 1,
              }}
            >
              <Tooltip direction="top" offset={[0, -3]}>
                {amenity.name} · {amenity.category}
              </Tooltip>
            </CircleMarker>
          );
        })}
        {routePositions.length > 1 && (
          <Polyline
            positions={routePositions}
            pathOptions={{
              color: route?.mode === "DRIVING" ? "#2563eb" : "#7c3aed",
              weight: 5,
              opacity: 0.85,
            }}
          >
            <Tooltip sticky>
              {route?.durationMinutes ?? "—"} min · {route?.distanceKm ?? "—"} km
            </Tooltip>
          </Polyline>
        )}
      </MapContainer>
      {onRefresh && (
        <button
          className="button small map-refresh-button"
          onClick={onRefresh}
          disabled={refreshing}
          title="Refresh subzone and HDB data"
        >
          Refresh
        </button>
      )}
      {amenities.length > 0 && (
        <details className="amenity-controls">
          <summary>Nearby amenities</summary>
          <div className="amenity-group-list">
            {AMENITY_GROUPS.map((group) => (
              <label className="amenity-toggle" key={group.id}>
                <input
                  type="checkbox"
                  checked={visibleGroups.includes(group.id)}
                  onChange={() => toggleGroup(group.id)}
                />
                <span
                  className="amenity-dot"
                  style={{ backgroundColor: group.color }}
                  aria-hidden="true"
                />
                {group.label}
              </label>
            ))}
          </div>
          <p className="amenity-count">{visibleAmenities.length} points shown</p>
        </details>
      )}
      <div className="map-legend" aria-label="Suitability score legend">
        <span>Score</span>
        <span className="legend-swatch" style={{ backgroundColor: "#dc2626" }} /> 0–29
        <span className="legend-swatch" style={{ backgroundColor: "#f59e0b" }} /> 30–59
        <span className="legend-swatch" style={{ backgroundColor: "#65a30d" }} /> 60–74
        <span className="legend-swatch" style={{ backgroundColor: "#0f766e" }} /> 75–100
      </div>
    </section>
  );
}

function styleFeature(
  feature: Feature | undefined,
  scores: Record<string, number>,
  selectedId: string | null,
  highlightedIds: string[],
): PathOptions {
  const code = (feature?.properties as { subzoneCode?: string } | undefined)?.subzoneCode;
  const score = code ? scores[code] : undefined;
  const selected = code === selectedId;
  const highlighted = code ? highlightedIds.includes(code) : false;
  return {
    fillColor: scoreColor(score),
    fillOpacity:
      score === undefined ? 0.18 : selected ? 0.82 : highlighted ? 0.78 : 0.55,
    color: selected ? "#000000" : highlighted ? "#f59e0b" : "#ffffff",
    weight: selected ? 3 : highlighted ? 2.5 : 1,
    opacity: 0.9,
    lineJoin: "round",
  };
}

function bindFeature(
  feature: Feature | undefined,
  layer: Layer,
  onSelect: (subzoneId: string) => void,
): void {
  const properties = (feature?.properties ?? {}) as {
    subzoneCode?: string;
    subzoneName?: string;
  };
  if (!properties.subzoneCode) {
    return;
  }
  layer.bindTooltip(
    `<strong>${escapeHtml(properties.subzoneName ?? properties.subzoneCode)}</strong><br/>Click for factsheet`,
    { sticky: true },
  );
  layer.on("click", () => onSelect(properties.subzoneCode as string));
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => {
    const entities: Record<string, string> = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    };
    return entities[character] ?? character;
  });
}
