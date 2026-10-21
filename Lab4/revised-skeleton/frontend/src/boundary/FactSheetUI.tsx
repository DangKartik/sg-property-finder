import type { NeighborhoodDetailsApi } from "../api/contracts";
import type {
  AmenityInfoDTO,
  CommuteEstimateDTO,
  EnvironmentInfoDTO,
  HousePricingDTO,
} from "../types/dto";

// React component; implementation deferred.
export declare class FactSheetUI {
  detailsApi: NeighborhoodDetailsApi;
  activeSubzoneId: string;

  constructor(detailsApi: NeighborhoodDetailsApi);

  displayDetails(
    amenities: AmenityInfoDTO[],
    env: EnvironmentInfoDTO,
    pricing: Record<string, HousePricingDTO>,
    commute: CommuteEstimateDTO,
  ): void;
}
