export interface CoordinatesDTO {
  latitude: number;
  longitude: number;
}

export interface AddressMatchDTO {
  formattedAddress: string;
  postalCode: string;
  coordinates: CoordinatesDTO;
  confidenceScore: number | null;
}

export type TransitModeDTO = "PUBLIC_TRANSIT" | "DRIVING" | "WALKING";

export type EnvironmentGranularityDTO = "NATIONAL" | "REGION" | "SUBZONE";

export type WarningSeverityDTO = "INFO" | "WARNING" | "ERROR";

export type DataAvailabilityCodeDTO =
  | "MISSING_SOURCE_DATA"
  | "VALID_ZERO"
  | "STALE_CACHE"
  | "PARTIAL_DATA";

export type CriterionDirectionDTO = "MINIMIZE" | "MAXIMIZE";

export interface CriterionDefinitionDTO {
  criterionId: string;
  criterionName: string;
  unit: string;
  direction: CriterionDirectionDTO;
  bufferM: number | null;
  defaultWeight: number | null;
}

export interface CriterionWeightDTO {
  criterionId: string;
  weightValue: number;
}

export interface CriterionScoreDTO {
  criterionId: string;
  criterionName: string;
  rawValue: number;
  normalisedScore: number;
  weight: number;
  weightedScore: number;
  isMissing: boolean;
  source: string;
}

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

export interface ValidationErrorDTO {
  field: string;
  message: string;
}

export interface ValidationResultDTO {
  isValid: boolean;
  errors: ValidationErrorDTO[];
}

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

export interface AmenityInfoDTO {
  amenityName: string;
  category: string;
  location: CoordinatesDTO;
  distanceKm: number | null;
}

export interface HousePricingDTO {
  averagePrice: number;
  medianPricePerSqm: number;
  priceTrend: string;
  priceTrendPercent: number;
  flatType: string;
  transactionCount: number;
  isTownProxy: boolean;
  dataWindowMonths: number;
  asOf: string | null;
}

export interface EnvironmentInfoDTO {
  weatherPattern: string;
  greenCoveragePercent: number;
  pm25: number | null;
  uvi: number | null;
  forecastCode: string | null;
  granularity: EnvironmentGranularityDTO;
  asOf: string | null;
}

export interface CommuteEstimateDTO {
  durationMinutes: number;
  distanceKm: number;
  transferCount: number;
  travelMode: TransitModeDTO;
  departureTime: string | null;
  routeGeometry: string | null;
}

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

export interface RecommendationItemDTO {
  subzoneId: string;
  subzoneName: string;
  rank: number;
  totalScore: number;
  criterionScores: CriterionScoreDTO[];
}

export interface RecommendationSetDTO {
  profileId: string;
  generatedTime: string;
  dataSnapshotId: string;
  dataAsOf: string;
  items: RecommendationItemDTO[];
  warnings: DataAvailabilityWarningDTO[];
}

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
}

export interface ComparisonResultDTO {
  profileId: string;
  generatedTime: string;
  items: RecommendationItemDTO[];
  details: NeighborhoodDetailDTO[];
  bestSubzoneId: string | null;
  summary: string;
}

export interface MapDataDTO {
  geojson: unknown;
  scores: Record<string, number>;
  center: CoordinatesDTO;
}

export interface RouteDataDTO {
  geometry: string;
  distanceKm: number;
  durationMinutes: number;
  mode: TransitModeDTO;
}

export interface PdfReportDTO {
  reportId: string;
  generatedTime: string;
  downloadUrl: string;
  expiresAt: string;
  fileName: string;
  contentType: string;
  sizeBytes: number;
}

export interface ApiErrorDTO {
  code: string;
  message: string;
  details: Record<string, unknown> | null;
}

export interface ApiEnvelope<T> {
  success: boolean;
  data: T | null;
  warnings: DataAvailabilityWarningDTO[];
  error: ApiErrorDTO | null;
}
