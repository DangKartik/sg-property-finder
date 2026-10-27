import type {
  AddressSearchApi,
  AmenitiesApi,
  ComparisonApi,
  CriteriaApi,
  DataStatusApi,
  MapApi,
  NeighborhoodDetailsApi,
  ProfileValidationApi,
  RankingApi,
  ReportApi,
  ShareApi,
} from "./contracts";
import { ApiCache, type CachedApiResponse } from "../container/ApiCache";
import type {
  AddressMatchDTO,
  AmenityPointDTO,
  ApiEnvelope,
  ComparisonResultDTO,
  CoordinatesDTO,
  CriterionDefinitionDTO,
  DataAvailabilityWarningDTO,
  DataStatusMapDTO,
  MapDataDTO,
  NeighborhoodDetailDTO,
  PdfReportDTO,
  ProfileDTO,
  RecommendationSetDTO,
  ReportResponseDTO,
  RouteDataDTO,
  ShareScenarioDTO,
  ValidationResultDTO,
} from "../types/dto";

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";
export const apiCache = new ApiCache();
let cachePruned = false;

const CACHE_TTLS = {
  criteria: 24 * 60 * 60 * 1000,
  geometry: 60 * 60 * 1000,
  amenities: 60 * 60 * 1000,
  factsheet: 10 * 60 * 1000,
  recommendations: 5 * 60 * 1000,
  comparison: 5 * 60 * 1000,
  route: 30 * 60 * 1000,
} as const;

export interface RequestCacheOptions {
  ttlMs: number;
}

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

async function request<T>(
  path: string,
  init?: RequestInit,
  cacheOptions?: RequestCacheOptions,
): Promise<ApiEnvelope<T>> {
  const method = (init?.method ?? "GET").toUpperCase();
  const cacheKey = cacheOptions ? cacheKeyFor(method, path, init?.body) : null;

  if (cacheOptions && !cachePruned) {
    cachePruned = true;
    void apiCache.prune();
  }

  const cached = cacheKey ? await apiCache.get(cacheKey) : undefined;
  if (cached && Date.now() < cached.expiresAt) {
    return cached.envelope as ApiEnvelope<T>;
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (cached?.etag && method === "GET") {
    headers["If-None-Match"] = cached.etag;
  }

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers,
    });
  } catch {
    if (cached) {
      return staleEnvelope<T>(cached);
    }
    throw new ApiRequestError(
      "Cannot reach the backend. Is FastAPI running on port 8000?",
      "NETWORK_ERROR",
      true,
    );
  }

  if (response.status === 304 && cached && cacheOptions) {
    const now = Date.now();
    await apiCache.set({
      ...cached,
      storedAt: now,
      expiresAt: now + cacheOptions.ttlMs,
    });
    return cached.envelope as ApiEnvelope<T>;
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

  if (
    cacheKey &&
    cacheOptions &&
    payload.success &&
    payload.data !== null &&
    payload.data !== undefined
  ) {
    const now = Date.now();
    await apiCache.set({
      key: cacheKey,
      envelope: payload as ApiEnvelope<unknown>,
      etag: response.headers.get("ETag"),
      storedAt: now,
      expiresAt: now + cacheOptions.ttlMs,
    });
  }

  return payload;
}

function cacheKeyFor(method: string, path: string, body: BodyInit | null | undefined): string {
  const bodyKey = body ? `:${hashString(String(body))}` : "";
  return `v2:${method}:${path}${bodyKey}`;
}

function hashString(value: string): string {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(36);
}

function staleEnvelope<T>(cached: CachedApiResponse): ApiEnvelope<T> {
  const warning: DataAvailabilityWarningDTO = {
    subzoneCode: null,
    datasetCode: "API_CACHE",
    code: "STALE_CACHE",
    severity: "WARNING",
    isStale: true,
    isRetryable: true,
    source: "IndexedDB",
    message: "Showing a cached response because the backend could not be reached.",
    asOf: new Date(cached.storedAt).toISOString(),
  };
  const envelope = cached.envelope as ApiEnvelope<T>;
  return {
    ...envelope,
    warnings: [...(envelope.warnings ?? []), warning],
  };
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
  AmenitiesApi &
  ProfileValidationApi &
  RankingApi &
  MapApi &
  NeighborhoodDetailsApi &
  ReportApi &
  ComparisonApi &
  ShareApi &
  DataStatusApi = {
  async getCriteria() {
    return request<CriterionDefinitionDTO[]>("/api/v1/criteria", undefined, {
      ttlMs: CACHE_TTLS.criteria,
    });
  },

  async getAmenities() {
    return request<AmenityPointDTO[]>("/api/v1/amenities", undefined, {
      ttlMs: CACHE_TTLS.amenities,
    });
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

  async decodeShare(share: string) {
    return request<ShareScenarioDTO>("/api/v1/share/decode", {
      method: "POST",
      body: JSON.stringify({ share }),
    });
  },

  async generateRankedRecommendations(profile: ProfileDTO) {
    return request<RecommendationSetDTO>(
      "/api/v1/recommendations",
      {
        method: "POST",
        body: JSON.stringify(profile),
      },
      { ttlMs: CACHE_TTLS.recommendations },
    );
  },

  async generateMapData(): Promise<ApiEnvelope<MapDataDTO>> {
    const envelope = await request<unknown>("/api/v1/subzones/geometry", undefined, {
      ttlMs: CACHE_TTLS.geometry,
    });
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
    return request<RouteDataDTO>(
      "/api/v1/commute/overlay",
      {
        method: "POST",
        body: JSON.stringify({ origin, destination, mode }),
      },
      { ttlMs: CACHE_TTLS.route },
    );
  },

  async fetchNeighborhoodDetails(subzoneCode: string, profile: ProfileDTO) {
    return request<NeighborhoodDetailDTO>(
      `/api/v1/subzones/${encodeURIComponent(subzoneCode)}/factsheet?profile=${queryProfile(profile)}`,
      undefined,
      { ttlMs: CACHE_TTLS.factsheet },
    );
  },

  async generatePdfReport(profile: ProfileDTO, subzoneCodes: string[]) {
    return request<ReportResponseDTO>("/api/v1/reports/pdf", {
      method: "POST",
      body: JSON.stringify({ profile, subzoneCodes }),
    });
  },

  async compare(profile: ProfileDTO, subzoneCodes: string[]) {
    return request<ComparisonResultDTO>(
      "/api/v1/comparison",
      {
        method: "POST",
        body: JSON.stringify({ profile, subzoneCodes }),
      },
      { ttlMs: CACHE_TTLS.comparison },
    );
  },

  async getStatus() {
    return request<DataStatusMapDTO>("/api/v1/data/status");
  },

  async refreshData() {
    const envelope = await request<DataStatusMapDTO>("/api/v1/data/refresh", {
      method: "POST",
    });
    if (envelope.success) {
      await apiCache.clear();
    }
    return envelope;
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
