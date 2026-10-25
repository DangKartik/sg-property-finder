import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ProfileFormUI } from "./ProfileFormUI";
import type { CriterionDefinitionDTO, ProfileDTO } from "../types/dto";

const criteria: CriterionDefinitionDTO[] = [
  { criterionId: "PRICE", criterionName: "Housing affordability", unit: "SGD", direction: "MINIMIZE", bufferM: null, defaultWeight: 5 },
  { criterionId: "COMMUTE_TIME", criterionName: "Commute duration", unit: "minutes", direction: "MINIMIZE", bufferM: null, defaultWeight: 5 },
  { criterionId: "SCHOOL_PROXIMITY", criterionName: "School access", unit: "count", direction: "MAXIMIZE", bufferM: 1000, defaultWeight: 5 },
  { criterionId: "GREEN_COVERAGE", criterionName: "Green coverage", unit: "percent", direction: "MAXIMIZE", bufferM: 500, defaultWeight: 5 },
  { criterionId: "AMENITIES_DENSITY", criterionName: "Amenity access", unit: "count", direction: "MAXIMIZE", bufferM: null, defaultWeight: 5 },
];

function profile(): ProfileDTO {
  return {
    profileId: "profile-1",
    profileName: "Test plan",
    budgetMin: 0,
    budgetMax: 800000,
    selectedFlatTypes: ["4 ROOM"],
    workplaceAddress: "Pasir Ris MRT",
    anchorCoordinates: { latitude: 1.3733, longitude: 103.9494 },
    criteriaWeights: criteria.map((criterion) => ({
      criterionId: criterion.criterionId,
      weightValue: 5,
    })),
    preferredCommuteMode: "PUBLIC_TRANSIT",
    departureTime: null,
    isActive: true,
    creationTime: null,
    lastUpdatedTime: null,
    minimumPrimarySchools: 2,
    minimumSecondarySchools: 1,
    minimumTertiarySchools: 1,
    minimumMalls: 3,
    minimumHospitals: 1,
  };
}

describe("ProfileFormUI hard minimums", () => {
  it("renders saved minimums and submits updated values", async () => {
    const createProfile = vi.fn().mockResolvedValue("profile-1");
    const updateProfile = vi.fn().mockResolvedValue(true);
    const onSaved = vi.fn();

    render(
      <ProfileFormUI
        profileControl={{ createProfile, updateProfile } as never}
        addressSearchApi={{} as never}
        criteria={criteria}
        initialProfile={profile()}
        onSaved={onSaved}
        onCancel={vi.fn()}
        onNotify={vi.fn()}
      />,
    );

    expect(screen.getByLabelText(/Primary schools/i)).toHaveValue(2);
    expect(screen.getByLabelText(/Tertiary schools/i)).toHaveValue(1);
    expect(screen.getByLabelText(/Hospitals/i)).toHaveValue(1);

    fireEvent.change(screen.getByLabelText(/Malls/i), { target: { value: "4" } });
    fireEvent.click(screen.getByRole("button", { name: /save & rank/i }));

    await waitFor(() => expect(updateProfile).toHaveBeenCalledTimes(1));
    expect(updateProfile.mock.calls[0][0]).toBe("profile-1");
    expect(updateProfile.mock.calls[0][1]).toMatchObject({
      minimumPrimarySchools: 2,
      minimumSecondarySchools: 1,
      minimumTertiarySchools: 1,
      minimumMalls: 4,
      minimumHospitals: 1,
    });
    expect(onSaved).toHaveBeenCalledWith("profile-1");
  });
});
