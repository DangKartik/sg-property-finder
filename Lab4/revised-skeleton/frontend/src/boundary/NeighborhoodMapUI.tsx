import type { MapApi } from "../api/contracts";
import type { CommuteEstimateDTO, CoordinatesDTO, SubzoneDTO } from "../types/dto";

// React + Leaflet component; implementation deferred.
export declare class NeighborhoodMapUI {
  mapApi: MapApi;
  choroplethLayers: Map<string, unknown>;
  mapCenterCoordinates: CoordinatesDTO;

  constructor(mapApi: MapApi);

  renderMap(subzones: SubzoneDTO[]): void;
  highlightSubzone(subzoneId: string): void;
  renderCommuteOverlay(estimate: CommuteEstimateDTO): void;
}
