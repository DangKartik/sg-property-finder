import type { MapApi } from "../api/contracts";
import type { CommuteEstimateDTO, CoordinatesDTO, SubzoneDTO } from "../types/dto";

/**
 * Stereotype: Boundary.
 * React-Leaflet map showing the URA subzone choropleth and commute overlays.
 */
export declare class NeighborhoodMapUI {
  /** Map data and route API. */
  mapApi: MapApi;

  /** Choropleth layers keyed by subzone code. */
  choroplethLayers: Map<string, unknown>;

  /** Initial map centre in WGS84 coordinates. */
  mapCenterCoordinates: CoordinatesDTO;

  /**
   * Create the map with its map API.
   * @param mapApi Map API.
   */
  constructor(mapApi: MapApi);

  /**
   * Render subzone polygons and suitability shading.
   * @param subzones Subzones returned by the backend.
   * @returns Nothing.
   */
  renderMap(subzones: SubzoneDTO[]): void;

  /**
   * Highlight one subzone on the map.
   * @param subzoneId Subzone code.
   * @returns Nothing.
   */
  highlightSubzone(subzoneId: string): void;

  /**
   * Draw a commute route overlay.
   * @param estimate Commute estimate containing route geometry.
   * @returns Nothing.
   */
  renderCommuteOverlay(estimate: CommuteEstimateDTO): void;
}
