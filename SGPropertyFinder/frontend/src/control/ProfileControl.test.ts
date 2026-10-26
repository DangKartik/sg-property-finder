import { beforeEach, describe, expect, it } from "vitest";
import { ProfileControl, ProfileValidationError } from "./ProfileControl";
import { ProfileCatalog } from "../container/ProfileCatalog";
import type { ProfileValidationApi } from "../api/contracts";
import type { ProfileDTO } from "../types/dto";

const acceptingValidator: ProfileValidationApi = {
  validateProfileData: async () => ({
    success: true,
    data: { isValid: true, errors: [] },
    warnings: [],
    error: null,
  }),
};

const rejectingValidator: ProfileValidationApi = {
  validateProfileData: async () => ({
    success: true,
    data: {
      isValid: false,
      errors: [
        {
          field: "budgetMax",
          message: "Budget maximum must be greater than zero.",
        },
      ],
    },
    warnings: [],
    error: null,
  }),
};

function makeProfile(overrides: Partial<ProfileDTO> = {}): ProfileDTO {
  return {
    profileId: "state-profile",
    profileName: "State Profile",
    budgetMin: 0,
    budgetMax: 600000,
    selectedFlatTypes: ["4 ROOM"],
    workplaceAddress: "Raffles Place",
    anchorCoordinates: { latitude: 1.283, longitude: 103.8513 },
    criteriaWeights: [
      { criterionId: "PRICE", weightValue: 5 },
      { criterionId: "COMMUTE_TIME", weightValue: 5 },
      { criterionId: "SCHOOL_PROXIMITY", weightValue: 5 },
      { criterionId: "GREEN_COVERAGE", weightValue: 5 },
      { criterionId: "AMENITIES_DENSITY", weightValue: 5 },
    ],
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
    ...overrides,
  };
}

async function clearProfiles(): Promise<void> {
  const catalog = new ProfileCatalog();
  const profiles = await catalog.loadFromLocalStorage();
  await Promise.all(
    profiles.map((profile) =>
      profile.profileId
        ? catalog.deleteProfile(profile.profileId)
        : Promise.resolve(false),
    ),
  );
}

describe("ProfileControl state-based black-box tests", () => {
  let catalog: ProfileCatalog;
  let control: ProfileControl;

  beforeEach(async () => {
    await clearProfiles();
    catalog = new ProfileCatalog();
    control = new ProfileControl(catalog, acceptingValidator);
  });

  // Independent transition tests: each starts from a fresh EMPTY state.
  it("BB-ST-FE-01 createProfile moves EMPTY to SAVED", async () => {
    const id = await control.createProfile(
      makeProfile({ profileId: "state-create" }),
    );

    expect(id).toBe("state-create");
    const saved = await catalog.getProfile(id);
    expect(saved?.profileName).toBe("State Profile");
    expect(saved?.creationTime).toBeTruthy();
    expect(saved?.lastUpdatedTime).toBeTruthy();
  });

  it("BB-ST-FE-02 loadFromLocalStorage reads a SAVED profile", async () => {
    await control.createProfile(
      makeProfile({ profileId: "state-read", profileName: "Read Plan" }),
    );

    const reloaded = new ProfileCatalog();
    const profiles = await reloaded.loadFromLocalStorage();

    expect(profiles).toHaveLength(1);
    expect(profiles[0].profileId).toBe("state-read");
    expect(profiles[0].profileName).toBe("Read Plan");
  });

  it("BB-ST-FE-03 updateProfile moves SAVED to UPDATED", async () => {
    const id = await control.createProfile(
      makeProfile({ profileId: "state-update", profileName: "Old Name" }),
    );

    const updated = await control.updateProfile(
      id,
      makeProfile({
        profileId: id,
        profileName: "New Name",
        budgetMax: 750000,
      }),
    );

    expect(updated).toBe(true);
    const saved = await catalog.getProfile(id);
    expect(saved?.profileName).toBe("New Name");
    expect(saved?.budgetMax).toBe(750000);
  });

  it("BB-ST-FE-04 deleteProfile moves SAVED to DELETED", async () => {
    const id = await control.createProfile(
      makeProfile({ profileId: "state-delete" }),
    );

    expect(await control.deleteProfile(id)).toBe(true);
    expect(await catalog.getProfile(id)).toBeUndefined();

    const reloaded = new ProfileCatalog();
    const profiles = await reloaded.loadFromLocalStorage();
    expect(profiles.some((profile) => profile.profileId === id)).toBe(false);
  });

  it("BB-ST-FE-05 rejected validation leaves SAVED state unchanged", async () => {
    const id = await control.createProfile(
      makeProfile({ profileId: "state-guard", profileName: "Guarded" }),
    );
    const guarded = new ProfileControl(catalog, rejectingValidator);

    await expect(
      guarded.updateProfile(
        id,
        makeProfile({ profileId: id, profileName: "Invalid", budgetMax: 0 }),
      ),
    ).rejects.toBeInstanceOf(ProfileValidationError);

    const saved = await catalog.getProfile(id);
    expect(saved?.profileName).toBe("Guarded");
    expect(saved?.budgetMax).toBe(600000);
  });

  it("BB-ST-FE-06 delete of an unknown profile stays in EMPTY", async () => {
    expect(await control.deleteProfile("state-missing")).toBe(false);
    expect(await catalog.getProfile("state-missing")).toBeUndefined();
  });

  // Cascading test: create -> read -> update -> read -> delete -> read deleted.
  it("BB-ST-FE-07 cascading profile lifecycle", async () => {
    const id = await control.createProfile(
      makeProfile({ profileId: "state-cascade", profileName: "Cascade" }),
    );
    expect((await catalog.getProfile(id))?.profileName).toBe("Cascade");

    const reader = new ProfileCatalog();
    const afterCreate = await reader.loadFromLocalStorage();
    expect(afterCreate.some((profile) => profile.profileId === id)).toBe(true);

    await control.updateProfile(
      id,
      makeProfile({ profileId: id, profileName: "Cascade Updated" }),
    );
    await reader.loadFromLocalStorage();
    const afterUpdate = await reader.getProfile(id);
    expect(afterUpdate?.profileName).toBe("Cascade Updated");

    expect(await control.deleteProfile(id)).toBe(true);
    await reader.loadFromLocalStorage();
    expect(await reader.getProfile(id)).toBeUndefined();

    const afterDelete = await new ProfileCatalog().loadFromLocalStorage();
    expect(afterDelete.some((profile) => profile.profileId === id)).toBe(false);
  });
});
