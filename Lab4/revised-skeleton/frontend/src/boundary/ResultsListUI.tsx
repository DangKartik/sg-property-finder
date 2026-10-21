import type { RecommendationSetDTO } from "../types/dto";
import { formatNumber, scoreColor } from "../utils/format";

export interface ResultsListUIProps {
  recommendationSet: RecommendationSetDTO | null;
  selectedSubzoneId: string | null;
  comparisonIds: string[];
  loading: boolean;
  onSelect: (subzoneId: string) => void;
  onToggleCompare: (subzoneId: string) => void;
  onOpenComparison: () => void;
  onOpenFactsheet: (subzoneId: string) => void;
}

/** Ranked subzone cards; synchronized with the map by subzone code. */
export function ResultsListUI({
  recommendationSet,
  selectedSubzoneId,
  comparisonIds,
  loading,
  onSelect,
  onToggleCompare,
  onOpenComparison,
  onOpenFactsheet,
}: ResultsListUIProps) {
  const items = recommendationSet?.items ?? [];

  return (
    <section className="panel results-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Recommendations</p>
          <h2>Best matches</h2>
        </div>
        <button
          className="button small"
          title={comparisonIds.length < 2 ? "Select at least two areas to compare" : "Open comparison"}
          onClick={onOpenComparison}
        >
          Compare ({comparisonIds.length})
        </button>
      </div>

      {loading && <div className="loading-line">Ranking neighbourhoods…</div>}
      {!loading && !recommendationSet && (
        <p className="muted">Select or create a plan to generate recommendations.</p>
      )}
      {!loading && recommendationSet && items.length === 0 && (
        <p className="muted">No subzones matched the current budget filter.</p>
      )}

      <div className="result-list">
        {items.map((item) => {
          const selected = item.subzoneId === selectedSubzoneId;
          const inComparison = comparisonIds.includes(item.subzoneId);
          return (
            <article
              id={`result-${item.subzoneId}`}
              key={item.subzoneId}
              className={`result-card ${selected ? "selected" : ""}`}
              onClick={() => onSelect(item.subzoneId)}
              tabIndex={0}
              role="button"
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelect(item.subzoneId);
                }
              }}
            >
              <div className="result-rank" style={{ backgroundColor: scoreColor(item.totalScore) }}>
                #{item.rank}
              </div>
              <div className="result-main">
                <div className="result-title-row">
                  <h3>{item.subzoneName}</h3>
                  <strong>{formatNumber(item.totalScore, 1)}</strong>
                </div>
                <div className="score-track" aria-hidden="true">
                  <span style={{ width: `${Math.max(2, item.totalScore)}%` }} />
                </div>
                <div className="result-actions">
                  <button
                    className="link-button"
                    onClick={(event) => {
                      event.stopPropagation();
                      onOpenFactsheet(item.subzoneId);
                    }}
                  >
                    View factsheet
                  </button>
                  <label
                    className="compare-toggle"
                    onClick={(event) => event.stopPropagation()}
                    title="Add this neighbourhood to the comparison matrix"
                  >
                    <input
                      type="checkbox"
                      checked={inComparison}
                      onChange={() => onToggleCompare(item.subzoneId)}
                    />
                    Compare
                  </label>
                </div>
              </div>
            </article>
          );
        })}
      </div>

      {recommendationSet && recommendationSet.warnings.length > 0 && (
        <p className="hint warning-text">
          {recommendationSet.warnings.length} data warning
          {recommendationSet.warnings.length === 1 ? "" : "s"} — check factsheets for missing data.
        </p>
      )}
    </section>
  );
}
