import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ResultsListUI } from "./ResultsListUI";
import type { RecommendationSetDTO } from "../types/dto";

function recommendationSet(count: number): RecommendationSetDTO {
  return {
    profileId: "profile-1",
    generatedTime: "2026-10-22T08:30:00+08:00",
    dataSnapshotId: "snapshot-1",
    dataAsOf: "2026-10-22T08:00:00+08:00",
    items: Array.from({ length: count }, (_, index) => ({
      subzoneId: `SZ${index + 1}`,
      subzoneName: `Subzone ${index + 1}`,
      rank: index + 1,
      totalScore: 100 - index,
      criterionScores: [],
    })),
    warnings: [],
    profileSnapshot: null,
  };
}

describe("ResultsListUI", () => {
  it("renders the ranked cards and comparison controls", () => {
    const onToggleCompare = vi.fn();
    const onExport = vi.fn();
    const { container } = render(
      <ResultsListUI
        recommendationSet={recommendationSet(20)}
        selectedSubzoneId={null}
        comparisonIds={[]}
        loading={false}
        onSelect={vi.fn()}
        onToggleCompare={onToggleCompare}
        onOpenComparison={vi.fn()}
        onOpenFactsheet={vi.fn()}
        onExport={onExport}
        exportDisabled={false}
      />,
    );

    expect(container.querySelectorAll(".result-card")).toHaveLength(20);
    expect(screen.getByText("Subzone 1")).toBeInTheDocument();
    expect(screen.getByText("Subzone 20")).toBeInTheDocument();

    fireEvent.click(screen.getAllByRole("checkbox")[0]);
    expect(onToggleCompare).toHaveBeenCalledWith("SZ1");

    fireEvent.click(screen.getByRole("button", { name: /export recommendations to pdf/i }));
    expect(onExport).toHaveBeenCalledTimes(1);
  });

  it("shows the warning count when the response has warnings", () => {
    const data = recommendationSet(2);
    data.warnings = [
      {
        subzoneCode: "SZ1",
        datasetCode: "COMMUTE",
        code: "ESTIMATED_COMMUTE_FALLBACK",
        severity: "WARNING",
        isStale: false,
        isRetryable: true,
        source: "Spatial estimate",
        message: "Estimated commute",
        asOf: null,
      },
    ];

    render(
      <ResultsListUI
        recommendationSet={data}
        selectedSubzoneId={null}
        comparisonIds={[]}
        loading={false}
        onSelect={vi.fn()}
        onToggleCompare={vi.fn()}
        onOpenComparison={vi.fn()}
        onOpenFactsheet={vi.fn()}
        onExport={vi.fn()}
        exportDisabled={false}
      />,
    );

    expect(screen.getByText(/1 data warning/i)).toBeInTheDocument();
  });
});
