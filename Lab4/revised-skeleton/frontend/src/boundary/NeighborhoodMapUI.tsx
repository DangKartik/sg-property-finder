import type { Feature, GeoJsonObject } from "geojson";
import type { Layer, PathOptions } from "leaflet";
import { GeoJSON, MapContainer, Polyline, TileLayer, Tooltip } from "react-leaflet";
import type { CoordinatesDTO, MapDataDTO, RouteDataDTO } from "../types/dto";
import { decodePolyline } from "../utils/polyline";
import { scoreColor } from "../utils/format";

export interface NeighborhoodMapUIProps {
  mapData: MapDataDTO | null;
  scores: Record<string, number>;
  selectedSubzoneId: string | null;
  highlightedSubzoneIds?: string[];
  route: RouteDataDTO | null;
  routeOrigin: CoordinatesDTO | null;
  routeDestination: CoordinatesDTO | null;
  onSelect: (subzoneId: string) => void;
}

const SINGAPORE_CENTER: [number, number] = [1.3521, 103.8198];

/** OneMap-backed Leaflet map with a subzone choropleth and route overlay. */
export function NeighborhoodMapUI({
  mapData,
  scores,
  selectedSubzoneId,
  highlightedSubzoneIds = [],
  route,
  routeOrigin,
  routeDestination,
  onSelect,
}: NeighborhoodMapUIProps) {
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

  return (
    <section className="map-panel" aria-label="Neighbourhood suitability map">
      <MapContainer center={center} zoom={11} scrollWheelZoom className="leaflet-container">
        <TileLayer
          attribution='Map data &copy; <a href="https://www.onemap.gov.sg/">OneMap Singapore</a>'
          url="https://www.onemap.gov.sg/maps/tiles/Default/{z}/{x}/{y}.png"
          maxZoom={19}
        />
        {mapData && (
          <GeoJSON
            key={`${selectedSubzoneId ?? "none"}-${highlightedSubzoneIds.join(",")}-${JSON.stringify(scores)}`}
            data={mapData.geojson as GeoJsonObject}
            style={(feature) =>
              styleFeature(feature, scores, selectedSubzoneId, highlightedSubzoneIds)
            }
            onEachFeature={(feature, layer) => bindFeature(feature, layer, onSelect)}
          />
        )}
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
    color: selected ? "#0f172a" : highlighted ? "#f59e0b" : "#ffffff",
    weight: selected ? 3 : highlighted ? 2.5 : 1,
    opacity: 0.9,
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
