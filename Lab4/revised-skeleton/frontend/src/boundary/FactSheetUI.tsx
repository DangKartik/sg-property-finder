import { useEffect, useState } from "react";
import type { NeighborhoodDetailsApi } from "../api/contracts";
import { requireData } from "../api/client";
import type { NeighborhoodDetailDTO, ProfileDTO } from "../types/dto";
import { formatDate, formatNumber, formatPrice } from "../utils/format";

export interface FactSheetUIProps {
  subzoneCode: string | null;
  profile: ProfileDTO;
  detailsApi: NeighborhoodDetailsApi;
  onClose: () => void;
  onNotify: (title: string, message: string) => void;
}

/** Modal factsheet with pricing, amenities, environment and commute details. */
export function FactSheetUI({
  subzoneCode,
  profile,
  detailsApi,
  onClose,
  onNotify,
}: FactSheetUIProps) {
  const [detail, setDetail] = useState<NeighborhoodDetailDTO | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!subzoneCode) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    detailsApi
      .fetchNeighborhoodDetails(subzoneCode, profile)
      .then((envelope) => {
        if (cancelled) return;
        try {
          setDetail(requireData(envelope));
        } catch (err) {
          const message = err instanceof Error ? err.message : "Unable to load factsheet.";
          setError(message);
          onNotify("Factsheet unavailable", message);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : "Unable to load factsheet.";
          setError(message);
          onNotify("Factsheet unavailable", message);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [subzoneCode, profile, detailsApi, onNotify]);

  if (!subzoneCode) {
    return null;
  }

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="modal factsheet-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="factsheet-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="modal-header">
          <div>
            <p className="eyebrow">Neighbourhood factsheet</p>
            <h2 id="factsheet-title">{detail?.subzoneName ?? subzoneCode}</h2>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close factsheet">
            ×
          </button>
        </header>

        {loading && <div className="loading-line">Loading factsheet…</div>}
        {error && <div className="form-errors">{error}</div>}

        {detail && (
          <div className="factsheet-grid">
            <section className="fact-section wide">
              <div className="section-title-row">
                <h3>Pricing by flat type</h3>
                {detail.pricingNote && (
                  <span className="badge warning" title={detail.pricingNote}>
                    Town-level proxy
                  </span>
                )}
              </div>
              {Object.keys(detail.pricing).length === 0 ? (
                <p className="muted">No pricing data available for the selected flat types.</p>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Flat type</th>
                      <th>Median price</th>
                      <th>Median $/sqm</th>
                      <th>Trend</th>
                      <th>Transactions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(detail.pricing).map(([flatType, pricing]) => (
                      <tr key={flatType}>
                        <td>{flatType}</td>
                        <td>{formatPrice(pricing.medianPrice ?? pricing.averagePrice)}</td>
                        <td>{formatPrice(pricing.medianPricePerSqm)}</td>
                        <td>
                          {pricing.priceTrend} ({pricing.priceTrendPercent.toFixed(1)}%)
                        </td>
                        <td>{pricing.transactionCount}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
              {detail.pricingNote && <p className="hint">{detail.pricingNote}</p>}
            </section>

            <section className="fact-section">
              <h3>Environment</h3>
              <dl className="fact-list">
                <div><dt>Green coverage</dt><dd>{formatNumber(detail.environment.greenCoveragePercent, 1)}%</dd></div>
                <div><dt>Weather</dt><dd>{detail.environment.weatherPattern}</dd></div>
                <div><dt>PM2.5</dt><dd>{formatNumber(detail.environment.pm25, 1)} µg/m³</dd></div>
                <div><dt>UVI</dt><dd>{formatNumber(detail.environment.uvi, 1)}</dd></div>
                <div><dt>Data as of</dt><dd>{formatDate(detail.environment.asOf)}</dd></div>
              </dl>
            </section>

            <section className="fact-section">
              <h3>Access & amenities</h3>
              <dl className="fact-list">
                <div><dt>Schools (1 km)</dt><dd>{detail.indicators?.primarySchoolCount1km ?? 0} primary · {detail.indicators?.secondarySchoolCount1km ?? 0} secondary</dd></div>
                <div><dt>Nearest school</dt><dd>{formatNumber(detail.indicators?.nearestSchoolM, 0)} m</dd></div>
                <div><dt>Hospitals (2 km)</dt><dd>{detail.indicators?.hospitalCount2km ?? 0}</dd></div>
                <div><dt>Malls (1 km)</dt><dd>{detail.indicators?.mallCount1km ?? 0}</dd></div>
                <div><dt>MRT (800 m)</dt><dd>{detail.indicators?.mrtStationCount800m ?? 0}</dd></div>
                <div><dt>Parks (500 m)</dt><dd>{detail.indicators?.parkCount500m ?? 0}</dd></div>
              </dl>
            </section>

            <section className="fact-section">
              <h3>Commute</h3>
              <dl className="fact-list">
                <div><dt>Mode</dt><dd>{detail.commute.travelMode.replace("_", " ")}</dd></div>
                <div><dt>Duration</dt><dd>{detail.commute.durationMinutes} min</dd></div>
                <div><dt>Distance</dt><dd>{detail.commute.distanceKm} km</dd></div>
                <div><dt>Transfers</dt><dd>{detail.commute.transferCount}</dd></div>
              </dl>
            </section>

            <section className="fact-section wide">
              <h3>Amenities nearby</h3>
              {detail.amenities.length === 0 ? (
                <p className="muted">No amenity points are available for this subzone.</p>
              ) : (
                <div className="amenity-chips">
                  {detail.amenities.slice(0, 18).map((amenity) => (
                    <span className="amenity-chip" key={`${amenity.category}-${amenity.amenityName}`}>
                      {amenity.amenityName}
                      <small>
                        {amenity.category}
                        {amenity.distanceKm !== null ? ` · ${amenity.distanceKm} km` : ""}
                      </small>
                    </span>
                  ))}
                </div>
              )}
            </section>

            {detail.warnings.length > 0 && (
              <section className="fact-section wide">
                <h3>Data warnings</h3>
                <div className="warning-list">
                  {detail.warnings.map((warning, index) => (
                    <span className={`badge ${warning.severity.toLowerCase()}`} key={`${warning.code}-${index}`}>
                      {warning.message}
                    </span>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}

        <footer className="modal-footer">
          <button className="button primary" onClick={onClose}>Close</button>
        </footer>
      </section>
    </div>
  );
}
