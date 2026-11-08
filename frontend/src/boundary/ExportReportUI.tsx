import { useEffect, useState } from "react";
import type { ReportApi } from "../api/contracts";
import { downloadReport, requireData } from "../api/client";
import type { ProfileDTO, RecommendationSetDTO, ReportResponseDTO } from "../types/dto";
import { formatDate } from "../utils/format";

export interface ExportReportUIProps {
  open: boolean;
  profile: ProfileDTO | null;
  recommendationSet: RecommendationSetDTO | null;
  subzoneCodes: string[];
  reportApi: ReportApi;
  onClose: () => void;
  onNotify: (title: string, message: string) => void;
}

/** PDF export modal with binary download and shareable URL. */
export function ExportReportUI({
  open,
  profile,
  recommendationSet,
  subzoneCodes,
  reportApi,
  onClose,
  onNotify,
}: ExportReportUIProps) {
  const [result, setResult] = useState<ReportResponseDTO | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!open) {
      setResult(null);
      setError(null);
      setCopied(false);
    }
  }, [open]);

  if (!open) {
    return null;
  }

  const codes = subzoneCodes.length
    ? subzoneCodes
    : (recommendationSet?.items.slice(0, 3).map((item) => item.subzoneId) ?? []);

  async function generate() {
    if (!profile) {
      onNotify("No plan selected", "Select or save a preference plan first.");
      return;
    }
    if (codes.length === 0) {
      onNotify("No neighbourhoods selected", "Generate recommendations before exporting a report.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const envelope = await reportApi.generatePdfReport(profile, codes);
      setResult(requireData(envelope));
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to generate the PDF.";
      setError(message);
      onNotify("Report generation failed", message);
    } finally {
      setLoading(false);
    }
  }

  async function download() {
    if (!result) return;
    try {
      await downloadReport(result.report);
    } catch (err) {
      onNotify("Download failed", err instanceof Error ? err.message : "The report link may have expired.");
    }
  }

  async function copyShareUrl() {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result.shareUrl);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      onNotify("Copy failed", "Select the share URL and copy it manually.");
    }
  }

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="modal export-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="export-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="modal-header">
          <div>
            <p className="eyebrow">Export</p>
            <h2 id="export-title">Download your report</h2>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close export modal">
            ×
          </button>
        </header>

        <p className="muted">
          Includes {codes.length} selected neighbourhood{codes.length === 1 ? "" : "s"} and the
          latest recommendation snapshot.
        </p>
        {error && <div className="form-errors">{error}</div>}

        {!result ? (
          <div className="export-empty">
            <button className="button primary" onClick={() => void generate()} disabled={loading}>
              {loading ? "Generating PDF…" : "Generate PDF"}
            </button>
          </div>
        ) : (
          <div className="export-result">
            <p role="status">Report generated successfully.</p>
            <div>
              <strong>{result.report.fileName}</strong>
              <p className="muted">
                {(result.report.sizeBytes / 1024).toFixed(1)} KB · expires{" "}
                {formatDate(result.report.expiresAt)}
              </p>
            </div>
            <div className="export-actions">
              <button className="button primary" onClick={() => void download()}>
                Download PDF
              </button>
              <button className="button" onClick={() => void copyShareUrl()}>
                {copied ? "Copied" : "Copy share URL"}
              </button>
            </div>
            <label className="field">
              <span>Shareable scenario</span>
              <input readOnly value={result.shareUrl} onFocus={(event) => event.target.select()} />
            </label>
          </div>
        )}

        <footer className="modal-footer">
          <button className="button" onClick={onClose}>Close</button>
        </footer>
      </section>
    </div>
  );
}
