import type { ReportApi } from "../api/contracts";
import type {
  ApiEnvelope,
  NeighborhoodDetailDTO,
  PdfReportDTO,
  RecommendationSetDTO,
} from "../types/dto";

/**
 * Stereotype: Boundary.
 * Export modal that requests a PDF and exposes a secure download link.
 */
export declare class ExportReportUI {
  /** Report generation API. */
  reportApi: ReportApi;

  /** Export format; currently `pdf`. */
  reportFormat: string;

  /**
   * Create the export modal with its report API.
   * @param reportApi Report API.
   */
  constructor(reportApi: ReportApi);

  /**
   * Render the export modal.
   * @returns Nothing.
   */
  renderExportModal(): void;

  /**
   * Request PDF generation.
   * @param recommendations Recommendation set to include.
   * @param details Factsheets for the selected subzones.
   * @returns Envelope containing secure download metadata.
   * @throws When report generation fails.
   */
  triggerPdfExport(
    recommendations: RecommendationSetDTO,
    details: NeighborhoodDetailDTO[],
  ): Promise<ApiEnvelope<PdfReportDTO>>;

  /**
   * Display the secure download link.
   * @param downloadUrl Short-lived report URL.
   * @returns Nothing.
   */
  displayDownloadLink(downloadUrl: string): void;
}
