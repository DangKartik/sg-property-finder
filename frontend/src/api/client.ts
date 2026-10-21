import type {
  AddressSearchApi,
  ComparisonApi,
  CriteriaApi,
  DataStatusApi,
  MapApi,
  NeighborhoodDetailsApi,
  ProfileValidationApi,
  RankingApi,
  ReportApi,
} from "./contracts";
import type {
  AddressMatchDTO,
  ApiEnvelope,
  ComparisonResultDTO,
  CoordinatesDTO,
  CriterionDefinitionDTO,
  DataStatusMapDTO,
  MapDataDTO,
  NeighborhoodDetailDTO,
  PdfReportDTO,
  ProfileDTO,
  RecommendationSetDTO,
  ReportResponseDTO,
  RouteDataDTO,
  ValidationResultDTO,
} from "../types/dto";

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";

export class ApiRequestError extends Error {
  readonly code: string;
  readonly retryable: boolean;

  constructor(message: string, code = "API_ERROR", retryable = false) {
    super(message);
    this.name = "ApiRequestError";
    this.code = code;
    this.retryable = retryable;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<ApiEnvelope<T>> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
    });
  } catch (error) {
    throw new ApiRequestError(
      "Cannot reach the backend. Is FastAPI running on port 8000?",
      "NETWORK_ERROR",
      true,
    );
  }

  let payload: ApiEnvelope<T>;
  try {
    payload = (await response.json()) as ApiEnvelope<T>;
  } catch {
    throw new ApiRequestError(`Backend returned HTTP ${response.status}.`, "BAD_RESPONSE");
  }

  if (!payload || typeof payload !== "object") {
    throw new ApiRequestError("Backend returned an invalid response.", "BAD_RESPONSE");
  }
  return payload;
}

export function requireData<T>(envelope: ApiEnvelope<T>): T {
  if (!envelope.success || envelope.data === null || envelope.data === undefined) {
    throw new ApiRequestError(
      envelope.error?.message ?? "Request failed.",
      envelope.error?.code ?? "API_ERROR",
      Boolean(envelope.error?.details && (envelope.error.details as { retryable?: boolean }).retryable),
    );
  }
  return envelope.data;
}

function queryProfile(profile: ProfileDTO): string {
  return encodeURIComponent(JSON.stringify(profile));
}

export const api: CriteriaApi &
  AddressSearchApi &
  ProfileValidationApi &
  RankingApi &
  MapApi &
  NeighborhoodDetailsApi &
  ReportApi &
  ComparisonApi &
  DataStatusApi = {
  async getCriteria() {
    return request<CriterionDefinitionDTO[]>("/api/v1/criteria");
  },

  async searchAddress(query: string) {
    return request<AddressMatchDTO[]>("/api/v1/address/search", {
      method: "POST",
      body: JSON.stringify({ query }),
    });
  },

  async validateProfileData(data: ProfileDTO) {
    return request<ValidationResultDTO>("/api/v1/profiles/validate", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async generateRankedRecommendations(profile: ProfileDTO) {
    return request<RecommendationSetDTO>("/api/v1/recommendations", {
      method: "POST",
      body: JSON.stringify(profile),
    });
  },

  async generateMapData(): Promise<ApiEnvelope<MapDataDTO>> {
    const envelope = await request<unknown>("/api/v1/subzones/geometry");
    if (!envelope.success || !envelope.data) {
      return { ...envelope, data: null } as ApiEnvelope<MapDataDTO>;
    }
    return {
      ...envelope,
      data: {
        geojson: envelope.data,
        scores: {},
        center: { latitude: 1.3521, longitude: 103.8198 },
      },
    };
  },

  async fetchSubzoneBoundary(subzoneCode: string) {
    const envelope = await this.generateMapData();
    if (!envelope.success || !envelope.data) {
      return { ...envelope, data: null } as ApiEnvelope<unknown>;
    }
    const collection = envelope.data.geojson as {
      features?: Array<{ properties?: { subzoneCode?: string }; geometry?: unknown }>;
    };
    const feature = collection.features?.find(
      (item) => item.properties?.subzoneCode === subzoneCode,
    );
    return {
      success: Boolean(feature),
      data: feature?.geometry ?? null,
      warnings: envelope.warnings,
      error: feature ? null : { code: "SUBZONE_NOT_FOUND", message: "Subzone not found", details: null },
    };
  },

  async getCommuteOverlay(origin: CoordinatesDTO, destination: CoordinatesDTO, mode: string) {
    return request<RouteDataDTO>("/api/v1/commute/overlay", {
      method: "POST",
      body: JSON.stringify({ origin, destination, mode }),
    });
  },

  async fetchNeighborhoodDetails(subzoneCode: string, profile: ProfileDTO) {
    return request<NeighborhoodDetailDTO>(
      `/api/v1/subzones/${encodeURIComponent(subzoneCode)}/factsheet?profile=${queryProfile(profile)}`,
    );
  },

  async generatePdfReport(profile: ProfileDTO, subzoneCodes: string[]) {
    return request<ReportResponseDTO>("/api/v1/reports/pdf", {
      method: "POST",
      body: JSON.stringify({ profile, subzoneCodes }),
    });
  },

  async compare(profile: ProfileDTO, subzoneCodes: string[]) {
    return request<ComparisonResultDTO>("/api/v1/comparison", {
      method: "POST",
      body: JSON.stringify({ profile, subzoneCodes }),
    });
  },

  async getStatus() {
    return request<DataStatusMapDTO>("/api/v1/data/status");
  },
};

export async function downloadReport(report: PdfReportDTO): Promise<void> {
  const response = await fetch(`${BASE_URL}${report.downloadUrl}`);
  if (!response.ok) {
    throw new ApiRequestError("The report download link has expired.", "REPORT_EXPIRED");
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = report.fileName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
