import { describe, expect, it } from "vitest";
import {
  DEFAULT_IMPORTANCE,
  clampImportance,
  importanceFromProfile,
  normalizeProfileWeights,
} from "./weights";
import type { ProfileDTO } from "../types/dto";

const ids = ["PRICE", "COMMUTE_TIME", "SCHOOL_PROXIMITY", "GREEN_COVERAGE", "AMENITIES_DENSITY"];

function profileWithWeights(weights: number[]): ProfileDTO {
  return {
    profileId: "profile-1",
    profileName: "Test",
    budgetMin: 0,
    budgetMax: 600000,
    selectedFlatTypes: ["4 ROOM"],
    workplaceAddress: "Raffles Place",
    anchorCoordinates: { latitude: 1.283, longitude: 103.8513 },
    criteriaWeights: ids.map((criterionId, index) => ({
      criterionId,
      weightValue: weights[index],
    })),
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

describe("weight/importance helpers", () => {
  it("clamps ratings to the 1–10 scale", () => {
    expect(clampImportance(0)).toBe(1);
    expect(clampImportance(11)).toBe(10);
    expect(clampImportance(7.6)).toBe(8);
    expect(clampImportance(Number.NaN)).toBe(DEFAULT_IMPORTANCE);
  });

  it("uses 5 as the default for missing ratings", () => {
    const ratings = importanceFromProfile([], ids);
    expect(Object.values(ratings)).toEqual([5, 5, 5, 5, 5]);
  });

  it("preserves new 1–10 ratings", () => {
    const ratings = importanceFromProfile(
      ids.map((criterionId, index) => ({ criterionId, weightValue: index + 1 })),
      ids,
    );
    expect(Object.values(ratings)).toEqual([1, 2, 3, 4, 5]);
  });

  it("migrates legacy 0–100 weights proportionally", () => {
    const ratings = importanceFromProfile(
      ids.map((criterionId) => ({ criterionId, weightValue: 20 })),
      ids,
    );
    expect(Object.values(ratings)).toEqual([2, 2, 2, 2, 2]);
  });

  it("normalises a stored profile before persistence", () => {
    const profile = normalizeProfileWeights(
      profileWithWeights([20, 20, 20, 20, 20]),
    );
    expect(profile.criteriaWeights.map((weight) => weight.weightValue)).toEqual([
      2, 2, 2, 2, 2,
    ]);
  });
});
