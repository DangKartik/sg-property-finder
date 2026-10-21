import type {
  AddressMatchDTO,
  ApiEnvelope,
  ComparisonResultDTO,
  CoordinatesDTO,
  CriterionDefinitionDTO,
  MapDataDTO,
  NeighborhoodDetailDTO,
  PdfReportDTO,
  ProfileDTO,
  RecommendationSetDTO,
  RouteDataDTO,
  ValidationResultDTO,
} from "../types/dto";

export interface CriteriaApi {
  getCriteria(): Promise<ApiEnvelope<CriterionDefinitionDTO[]>>;
}

export interface AddressSearchApi {
  searchAddress(query: string): Promise<ApiEnvelope<AddressMatchDTO[]>>;
}

export interface ProfileValidationApi {
  validateProfileData(data: ProfileDTO): Promise<ApiEnvelope<ValidationResultDTO>>;
}

export interface RankingApi {
  generateRankedRecommendations(
    profile: ProfileDTO,
  ): Promise<ApiEnvelope<RecommendationSetDTO>>;
}

export interface MapApi {
  generateMapData(): Promise<ApiEnvelope<MapDataDTO>>;
  fetchSubzoneBoundary(subzoneCode: string): Promise<ApiEnvelope<unknown>>;
  getCommuteOverlay(
    origin: CoordinatesDTO,
    destination: CoordinatesDTO,
    mode: string,
  ): Promise<ApiEnvelope<RouteDataDTO>>;
}

export interface NeighborhoodDetailsApi {
  fetchNeighborhoodDetails(
    subzoneCode: string,
    profile: ProfileDTO,
  ): Promise<ApiEnvelope<NeighborhoodDetailDTO>>;
}

export interface ReportApi {
  generatePdfReport(
    recommendations: RecommendationSetDTO,
    details: NeighborhoodDetailDTO[],
  ): Promise<ApiEnvelope<PdfReportDTO>>;
}

export interface ComparisonApi {
  compare(
    profile: ProfileDTO,
    subzoneCodes: string[],
  ): Promise<ApiEnvelope<ComparisonResultDTO>>;
}
