import { useEffect, useState } from "react";
import type { ComparisonApi } from "../api/contracts";
import { requireData } from "../api/client";
import type { ComparisonResultDTO, ProfileDTO } from "../types/dto";
import { formatNumber, formatPrice } from "../utils/format";
import { NotificationModalUI } from "./NotificationModalUI";

export interface ComparisonUIProps {
  open: boolean;
  profile: ProfileDTO | null;
  subzoneCodes: string[];
  comparisonApi: ComparisonApi;
  onClose: () => void;
  onNotify: (title: string, message: string) => void;
}

/** Side-by-side comparison matrix for two or more selected subzones. */
export function ComparisonUI({
  open,
  profile,
  subzoneCodes,
  comparisonApi,
  onClose,
  onNotify,
}: ComparisonUIProps) {
  const [result, setResult] = useState<ComparisonResultDTO | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || subzoneCodes.length < 2 || !profile) {
      setResult(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    comparisonApi
      .compare(profile, subzoneCodes)
      .then((envelope) => {
        if (cancelled) return;
        try {
          setResult(requireData(envelope));
        } catch (err) {
          const message = err instanceof Error ? err.message : "Unable to compare subzones.";
          setError(message);
          onNotify("Comparison failed", message);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : "Unable to compare subzones.";
          setError(message);
          onNotify("Comparison failed", message);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, profile, subzoneCodes, comparisonApi, onNotify]);

  if (!open) {
    return null;
  }

  if (subzoneCodes.length < 2) {
    return (
      <NotificationModalUI
        title="Select at least two areas"
        message="Choose two or more neighbourhoods in the results list before opening the comparison matrix."
        onClose={onClose}
      />
    );
  }

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="modal comparison-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="comparison-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="modal-header">
          <div>
            <p className="eyebrow">Side-by-side</p>
            <h2 id="comparison-title">Compare neighbourhoods</h2>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close comparison">
            ×
          </button>
        </header>

        {loading && <div className="loading-line">Building comparison…</div>}
        {error && <div className="form-errors">{error}</div>}
        {result && (
          <div className="comparison-scroll">
            <table className="data-table comparison-table">
              <thead>
                <tr>
                  <th>Metric</th>
                  {result.details.map((detail) => (
                    <th key={detail.subzoneCode}>
                      {detail.subzoneName}
                      {result.bestSubzoneId === detail.subzoneCode && (
                        <span className="badge active best-badge">Best</span>
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <th>Overall score</th>
                  {result.details.map((detail) => (
                    <td key={detail.subzoneCode}>
                      {formatNumber(
                        result.items.find((item) => item.subzoneId === detail.subzoneCode)?.totalScore,
                        1,
                      )}
                    </td>
                  ))}
                </tr>
                <tr>
                  <th>Commute</th>
                  {result.details.map((detail) => (
                    <td key={detail.subzoneCode}>
                      {detail.commute.durationMinutes} min · {detail.commute.distanceKm} km
                    </td>
                  ))}
                </tr>
                <tr>
                  <th>Pricing</th>
                  {result.details.map((detail) => (
                    <td key={detail.subzoneCode}>
                      {Object.entries(detail.pricing).length === 0 ? (
                        <span className="muted">No pricing</span>
                      ) : (
                        Object.entries(detail.pricing).map(([flatType, pricing]) => (
                          <div key={flatType}>
                            {flatType}: {formatPrice(pricing.medianPrice ?? pricing.averagePrice)}
                            {pricing.isTownProxy && <small className="proxy-label"> town proxy</small>}
                          </div>
                        ))
                      )}
                    </td>
                  ))}
                </tr>
                <tr>
                  <th>Green coverage</th>
                  {result.details.map((detail) => (
                    <td key={detail.subzoneCode}>
                      {formatNumber(detail.environment.greenCoveragePercent, 1)}%
                    </td>
                  ))}
                </tr>
                <tr>
                  <th>PM2.5</th>
                  {result.details.map((detail) => (
                    <td key={detail.subzoneCode}>
                      {formatNumber(detail.environment.pm25, 1)} µg/m³
                    </td>
                  ))}
                </tr>
                <tr>
                  <th>Schools (1 km)</th>
                  {result.details.map((detail) => (
                    <td key={detail.subzoneCode}>
                      {detail.indicators?.primarySchoolCount1km ?? 0} primary ·{" "}
                      {detail.indicators?.secondarySchoolCount1km ?? 0} secondary ·{" "}
                      {detail.indicators?.tertiarySchoolCount1km ?? 0} tertiary
                    </td>
                  ))}
                </tr>
                <tr>
                  <th>Hospitals (2 km)</th>
                  {result.details.map((detail) => (
                    <td key={detail.subzoneCode}>{detail.indicators?.hospitalCount2km ?? 0}</td>
                  ))}
                </tr>
                <tr>
                  <th>Malls (1 km)</th>
                  {result.details.map((detail) => (
                    <td key={detail.subzoneCode}>{detail.indicators?.mallCount1km ?? 0}</td>
                  ))}
                </tr>
                <tr>
                  <th>MRT (800 m)</th>
                  {result.details.map((detail) => (
                    <td key={detail.subzoneCode}>{detail.indicators?.mrtStationCount800m ?? 0}</td>
                  ))}
                </tr>
              </tbody>
            </table>
            <p className="muted comparison-summary">{result.summary}</p>
          </div>
        )}

        <footer className="modal-footer">
          <button className="button primary" onClick={onClose}>Close</button>
        </footer>
      </section>
    </div>
  );
}
