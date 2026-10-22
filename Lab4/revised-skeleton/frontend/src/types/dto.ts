/**
 * Stereotype: Entity/DTO.
 * Browser-facing transport types mirroring the backend response schemas.
 * All timestamps are ISO-8601 strings; all coordinates are WGS84.
 */

/** WGS84 latitude/longitude pair. */
export interface CoordinatesDTO {
  latitude: number;
  longitude: number;
}

/** A confirmed OneMap address match. */
export interface AddressMatchDTO {
  formattedAddress: string;
  postalCode: string;
  coordinates: CoordinatesDTO;
  /** Null when OneMap does not provide a confidence value. */
  confidenceScore: number | null;
}

/** Commute modes supported by the routing adapter. */
export type TransitModeDTO = "PUBLIC_TRANSIT" | "DRIVING" | "WALKING";

/** Spatial level at which environment data is reported. */
export type EnvironmentGranularityDTO = "NATIONAL" | "REGION" | "SUBZONE";

/** Severity of a data-availability warning. */
export type WarningSeverityDTO = "INFO" | "WARNING" | "ERROR";

/** Machine-readable reason for a data warning. */
export type DataAvailabilityCodeDTO =
  | "MISSING_SOURCE_DATA"
  | "VALID_ZERO"
  | "STALE_CACHE"
  | "PARTIAL_DATA"
  | "ESTIMATED_COMMUTE_FALLBACK";

/** Whether a criterion is minimised or maximised. */
export type CriterionDirectionDTO = "MINIMIZE" | "MAXIMIZE";

/** Frozen criterion metadata used by the form and scoring engine. */
export interface CriterionDefinitionDTO {
  criterionId: string;
  criterionName: string;
  unit: string;
  direction: CriterionDirectionDTO;
  /** Buffer radius in metres, or null when not spatial. */
  bufferM: number | null;
  /** Default weight in [0, 1], or null when no product default is set. */
  defaultWeight: number | null;
}

/** User-assigned weight for one criterion. */
export interface CriterionWeightDTO {
  criterionId: string;
  weightValue: number;
}

/** Per-criterion explanation of a suitability score. */
export interface CriterionScoreDTO {
  criterionId: string;
  rawValue: number;
  /** Normalised score in [0, 1]. */
  normalisedScore: number;
  /** Renormalised weight in [0, 1]. */
  weight: number;
  /** normalisedScore × weight. */
  weightedScore: number;
  isMissing: boolean;
  source: string;
}

/** Preference profile submitted to the backend. */
export interface ProfileDTO {
  profileId: string | null;
  profileName: string;
  budgetMin: number;
  budgetMax: number;
  selectedFlatTypes: string[];
  workplaceAddress: string | null;
  anchorCoordinates: CoordinatesDTO | null;
  criteriaWeights: CriterionWeightDTO[];
  preferredCommuteMode: TransitModeDTO;
  departureTime: string | null;
  isActive: boolean;
  creationTime: string | null;
  lastUpdatedTime: string | null;
}

/** Decoded shareable scenario returned by the backend. */
export interface ShareScenarioDTO {
  profile: ProfileDTO;
  subzoneCodes: string[];
}

/** One field-level validation error. */
export interface ValidationErrorDTO {
  field: string;
  message: string;
}

/** Result of validating a profile. */
export interface ValidationResultDTO {
  isValid: boolean;
  errors: ValidationErrorDTO[];
}

/** Missing, stale, partial or valid-zero data notice. */
export interface DataAvailabilityWarningDTO {
  subzoneCode: string | null;
  datasetCode: string;
  code: DataAvailabilityCodeDTO;
  severity: WarningSeverityDTO;
  isStale: boolean;
  isRetryable: boolean;
  source: string;
  message: string;
  asOf: string | null;
}

/** Amenity point returned for the map overlay. */
export interface AmenityPointDTO {
  name: string;
  category: string;
  latitude: number;
  longitude: number;
}

/** Amenity and its distance from the subzone anchor. */
export interface AmenityInfoDTO {
  amenityName: string;
  category: string;
  location: CoordinatesDTO;
  distanceKm: number | null;
}

/** HDB resale pricing for one flat type. */
export interface HousePricingDTO {
  averagePrice: number;
  medianPrice: number | null;
  medianPricePerSqm: number;
  priceTrend: string;
  priceTrendPercent: number;
  flatType: string;
  transactionCount: number;
  isTownProxy: boolean;
  dataWindowMonths: number;
  asOf: string | null;
}

/** Static and live environmental information. */
export interface EnvironmentInfoDTO {
  weatherPattern: string;
  greenCoveragePercent: number;
  pm25: number | null;
  uvi: number | null;
  forecastCode: string | null;
  granularity: EnvironmentGranularityDTO;
  asOf: string | null;
}

/** Commute duration, distance, transfers and optional route geometry. */
export interface CommuteEstimateDTO {
  durationMinutes: number;
  distanceKm: number;
  transferCount: number;
  travelMode: TransitModeDTO;
  departureTime: string | null;
  routeGeometry: string | null;
}

/** Subzone geometry and metadata. */
export interface SubzoneDTO {
  subzoneCode: string;
  subzoneName: string;
  planningAreaName: string;
  townName: string;
  boundaryGeoJson: unknown;
  regionName: string;
  centroid: CoordinatesDTO;
  indicators: SubzoneIndicatorsDTO | null;
}

/** Precomputed numeric features used by scoring. */
export interface SubzoneIndicatorsDTO {
  nearestParkM: number | null;
  parkCount500m: number;
  greenCoveragePercent500m: number | null;
  nearestSchoolM: number | null;
  primarySchoolCount1km: number;
  secondarySchoolCount1km: number;
  nearestPolyclinicM: number | null;
  polyclinicCount2km: number;
  nearestHospitalM: number | null;
  hospitalCount2km: number;
  nearestMallM: number | null;
  mallCount1km: number;
  nearestMrtM: number | null;
  mrtStationCount800m: number;
  parkConnectorLength1km: number;
  cyclingPathLength1km: number;
  medianResalePrice: number | null;
  medianPricePerSqm: number | null;
  transactionCount12m: number;
  priceTrendPercent: number | null;
  pm25Baseline: number | null;
  pm25Live: number | null;
  uvi: number | null;
  forecastCode: string | null;
  dataAsOf: string | null;
}

/** One ranked subzone with its score explanation. */
export interface RecommendationItemDTO {
  subzoneId: string;
  subzoneName: string;
  rank: number;
  totalScore: number;
  criterionScores: CriterionScoreDTO[];
}

/** Ranked recommendations for one profile snapshot. */
export interface RecommendationSetDTO {
  profileId: string;
  generatedTime: string;
  dataSnapshotId: string;
  dataAsOf: string;
  items: RecommendationItemDTO[];
  warnings: DataAvailabilityWarningDTO[];
  profileSnapshot: ProfileDTO | null;
}

/** Complete factsheet for one subzone. */
export interface NeighborhoodDetailDTO {
  subzoneCode: string;
  subzoneName: string;
  pricing: Record<string, HousePricingDTO>;
  amenities: AmenityInfoDTO[];
  environment: EnvironmentInfoDTO;
  commute: CommuteEstimateDTO;
  warnings: DataAvailabilityWarningDTO[];
  generatedTime: string;
  indicators: SubzoneIndicatorsDTO | null;
  pricingNote: string | null;
}

/** Side-by-side comparison result. */
export interface ComparisonResultDTO {
  profileId: string;
  generatedTime: string;
  items: RecommendationItemDTO[];
  details: NeighborhoodDetailDTO[];
  bestSubzoneId: string | null;
  summary: string;
}

/** Leaflet-ready map payload. */
export interface MapDataDTO {
  geojson: unknown;
  scores: Record<string, number>;
  center: CoordinatesDTO;
}

/** Route overlay payload. */
export interface RouteDataDTO {
  geometry: string;
  distanceKm: number;
  durationMinutes: number;
  mode: TransitModeDTO;
}

/** Browser-safe PDF report metadata. */
export interface PdfReportDTO {
  reportId: string;
  generatedTime: string;
  downloadUrl: string;
  expiresAt: string;
  fileName: string;
  contentType: string;
  sizeBytes: number;
}

/** PDF generation response, including the shareable scenario URL. */
export interface ReportResponseDTO {
  report: PdfReportDTO;
  shareUrl: string;
}

/** Freshness metadata for one backend dataset. */
export interface DatasetStatusDTO {
  datasetId: string;
  dataSnapshotId: string;
  dataAsOf: string;
  source: string;
  isStale: boolean;
  recordCount: number;
  lastError: string | null;
}

export type DataStatusMapDTO = Record<string, DatasetStatusDTO>;

/** Standard API error. */
export interface ApiErrorDTO {
  code: string;
  message: string;
  details: Record<string, unknown> | null;
}

/** Standard API response envelope. */
export interface ApiEnvelope<T> {
  success: boolean;
  data: T | null;
  warnings: DataAvailabilityWarningDTO[];
  error: ApiErrorDTO | null;
}
