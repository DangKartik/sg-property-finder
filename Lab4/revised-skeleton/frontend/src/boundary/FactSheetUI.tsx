import type { NeighborhoodDetailsApi } from "../api/contracts";
import type {
  AmenityInfoDTO,
  CommuteEstimateDTO,
  EnvironmentInfoDTO,
  HousePricingDTO,
} from "../types/dto";

/**
 * Stereotype: Boundary.
 * Modal showing multi-flat-type pricing, amenities, environment and commute
 * details for one subzone.
 */
export declare class FactSheetUI {
  /** Factsheet API. */
  detailsApi: NeighborhoodDetailsApi;

  /** Currently displayed subzone code. */
  activeSubzoneId: string;

  /**
   * Create the factsheet with its details API.
   * @param detailsApi Factsheet API.
   */
  constructor(detailsApi: NeighborhoodDetailsApi);

  /**
   * Display the fact sheet sections.
   *
   * When any pricing entry has `isTownProxy=true`, show the tooltip:
   * "Pricing data represents the median resale price for the overarching HDB Town."
   *
   * @param amenities Nearby amenities.
   * @param env Environment information.
   * @param pricing Pricing keyed by flat type.
   * @param commute Commute estimate.
   * @returns Nothing.
   */
  displayDetails(
    amenities: AmenityInfoDTO[],
    env: EnvironmentInfoDTO,
    pricing: Record<string, HousePricingDTO>,
    commute: CommuteEstimateDTO,
  ): void;
}
