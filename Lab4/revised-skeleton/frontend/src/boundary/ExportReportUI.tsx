import type { ReportApi } from "../api/contracts";
import type {
  ApiEnvelope,
  NeighborhoodDetailDTO,
  PdfReportDTO,
  RecommendationSetDTO,
} from "../types/dto";

// React component; implementation deferred.
export declare class ExportReportUI {
  reportApi: ReportApi;
  reportFormat: string;

  constructor(reportApi: ReportApi);

  renderExportModal(): void;
  triggerPdfExport(
    recommendations: RecommendationSetDTO,
    details: NeighborhoodDetailDTO[],
  ): Promise<ApiEnvelope<PdfReportDTO>>;
  displayDownloadLink(downloadUrl: string): void;
}
