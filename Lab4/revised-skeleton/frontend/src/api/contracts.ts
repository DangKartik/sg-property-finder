import type {
  AddressMatchDTO,
  AmenityPointDTO,
  ApiEnvelope,
  ComparisonResultDTO,
  CoordinatesDTO,
  CriterionDefinitionDTO,
  MapDataDTO,
  NeighborhoodDetailDTO,
  ProfileDTO,
  RecommendationSetDTO,
  ReportResponseDTO,
  RouteDataDTO,
  ShareScenarioDTO,
  ValidationResultDTO,
  DataStatusMapDTO,
} from "../types/dto";

/**
 * Stereotype: API contract.
 * Returns the frozen criterion catalogue used to render preference sliders.
 */
export interface CriteriaApi {
  /**
   * Load all criterion definitions.
   * @returns Envelope containing criterion definitions.
   * @throws When the API request fails.
   */
  getCriteria(): Promise<ApiEnvelope<CriterionDefinitionDTO[]>>;
}

/**
 * Stereotype: API contract.
 * OneMap-backed workplace address search.
 */
export interface AddressSearchApi {
  /**
   * Search for an address.
   * @param query Free-text address, building name or postal code.
   * @returns Envelope containing detailed address matches.
   * @throws When the API request fails.
   */
  searchAddress(query: string): Promise<ApiEnvelope<AddressMatchDTO[]>>;
}

/**
 * Stereotype: API contract.
 * Authoritative profile validation.
 */
export interface ProfileValidationApi {
  /**
   * Validate a profile.
   * @param data Profile to validate.
   * @returns Envelope containing field-level validation errors.
   * @throws When the API request fails.
   */
  validateProfileData(data: ProfileDTO): Promise<ApiEnvelope<ValidationResultDTO>>;
}

/**
 * Stereotype: API contract.
 * Recommendation generation.
 */
export interface RankingApi {
  /**
   * Generate ranked recommendations for a profile.
   * @param profile Profile input.
   * @returns Envelope containing the recommendation set.
   * @throws When the ranking request fails.
   */
  generateRankedRecommendations(
    profile: ProfileDTO,
  ): Promise<ApiEnvelope<RecommendationSetDTO>>;
}

/**
 * Stereotype: API contract.
 * Amenity points used by the map overlay layers.
 */
export interface AmenitiesApi {
  /**
   * Load all amenity points.
   * @returns Envelope containing amenity points.
   * @throws When the API request fails.
   */
  getAmenities(): Promise<ApiEnvelope<AmenityPointDTO[]>>;
}

/**
 * Stereotype: API contract.
 * Map geometry, choropleth scores and commute overlays.
 */
export interface MapApi {
  /**
   * Load subzone GeoJSON and scores.
   * @returns Envelope containing map data.
   * @throws When the API request fails.
   */
  generateMapData(): Promise<ApiEnvelope<MapDataDTO>>;

  /**
   * Load one subzone boundary.
   * @param subzoneCode Subzone code.
   * @returns Envelope containing GeoJSON geometry.
   * @throws When the subzone is unknown or the request fails.
   */
  fetchSubzoneBoundary(subzoneCode: string): Promise<ApiEnvelope<unknown>>;

  /**
   * Load a commute route overlay.
   * @param origin Start coordinate.
   * @param destination End coordinate.
   * @param mode Travel mode.
   * @returns Envelope containing route geometry.
   * @throws When no route exists or the request fails.
   */
  getCommuteOverlay(
    origin: CoordinatesDTO,
    destination: CoordinatesDTO,
    mode: string,
  ): Promise<ApiEnvelope<RouteDataDTO>>;
}

/**
 * Stereotype: API contract.
 * Subzone factsheet retrieval.
 */
export interface NeighborhoodDetailsApi {
  /**
   * Load a subzone factsheet.
   * @param subzoneCode Subzone code.
   * @param profile Profile providing flat types, workplace and commute mode.
   * @returns Envelope containing the factsheet.
   * @throws When the subzone is unknown or the request fails.
   */
  fetchNeighborhoodDetails(
    subzoneCode: string,
    profile: ProfileDTO,
  ): Promise<ApiEnvelope<NeighborhoodDetailDTO>>;
}

/**
 * Stereotype: API contract.
 * PDF report generation.
 */
export interface ReportApi {
  /**
   * Generate a PDF report for a profile and selected subzones.
   * @param profile Profile providing the report context.
   * @param subzoneCodes Subzones to include.
   * @returns Envelope containing secure download metadata and a share URL.
   * @throws When report generation fails.
   */
  generatePdfReport(
    profile: ProfileDTO,
    subzoneCodes: string[],
  ): Promise<ApiEnvelope<ReportResponseDTO>>;
}

/**
 * Stereotype: API contract.
 * Decodes a shareable scenario payload into a profile and subzone selection.
 */
export interface ShareApi {
  /**
   * Decode a `?share=` payload.
   * @param share URL-safe base64 share payload.
   * @returns Envelope containing the profile and shared subzone codes.
   * @throws When the payload is invalid or the request fails.
   */
  decodeShare(share: string): Promise<ApiEnvelope<ShareScenarioDTO>>;
}

/** Freshness/status API for the IndexedDB cache layer. */
export interface DataStatusApi {
  getStatus(): Promise<ApiEnvelope<DataStatusMapDTO>>;

  /**
   * Force a live data.gov.sg refresh of subzone and HDB snapshots.
   * @returns Envelope containing refreshed dataset statuses.
   * @throws When the refresh request fails.
   */
  refreshData(): Promise<ApiEnvelope<DataStatusMapDTO>>;
}

/**
 * Stereotype: API contract.
 * Side-by-side comparison.
 */
export interface ComparisonApi {
  /**
   * Compare selected subzones.
   * @param profile Profile providing comparison context.
   * @param subzoneCodes Two or more subzone codes.
   * @returns Envelope containing comparison items and full details.
   * @throws When fewer than two subzones are supplied or the request fails.
   */
  compare(
    profile: ProfileDTO,
    subzoneCodes: string[],
  ): Promise<ApiEnvelope<ComparisonResultDTO>>;
}
