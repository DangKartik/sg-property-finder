import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ExportReportUI } from "./ExportReportUI";
import type { ReportApi } from "../api/contracts";
import type { ProfileDTO, ReportResponseDTO } from "../types/dto";

function profile(): ProfileDTO {
  return {
    profileId: "profile-1",
    profileName: "Test plan",
    budgetMin: 0,
    budgetMax: 800000,
    selectedFlatTypes: ["4 ROOM"],
    workplaceAddress: "Pasir Ris MRT",
    anchorCoordinates: { latitude: 1.3733, longitude: 103.9494 },
    criteriaWeights: [{ criterionId: "PRICE", weightValue: 5 }],
    preferredCommuteMode: "PUBLIC_TRANSIT",
    departureTime: null,
    isActive: true,
    creationTime: null,
    lastUpdatedTime: null,
    minimumPrimarySchools: 0,
    minimumSecondarySchools: 0,
    minimumTertiarySchools: 0,
    minimumMalls: 0,
    minimumHospitals: 0,
  };
}

const generatedReport: ReportResponseDTO = {
  report: {
    reportId: "report-1",
    generatedTime: "2026-10-22T08:30:00+08:00",
    downloadUrl: "/api/v1/reports/download/report-1",
    expiresAt: "2026-10-22T08:45:00+08:00",
    fileName: "SGPropFinder_Report_report-1.pdf",
    contentType: "application/pdf",
    sizeBytes: 7068,
  },
  shareUrl: "http://localhost:5173/?share=scenario",
};

describe("ExportReportUI", () => {
  it("confirms a generated report with a success message", async () => {
    const reportApi: ReportApi = {
      generatePdfReport: vi.fn().mockResolvedValue({
        success: true,
        data: generatedReport,
        warnings: [],
        error: null,
      }),
    };
    render(
      <ExportReportUI
        open
        profile={profile()}
        recommendationSet={null}
        subzoneCodes={["SZ1"]}
        reportApi={reportApi}
        onClose={vi.fn()}
        onNotify={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Generate PDF" }));

    expect(await screen.findByText("Report generated successfully.")).toBeInTheDocument();
    expect(screen.getByText("SGPropFinder_Report_report-1.pdf")).toBeInTheDocument();
    expect(reportApi.generatePdfReport).toHaveBeenCalledWith(profile(), ["SZ1"]);
  });
});
