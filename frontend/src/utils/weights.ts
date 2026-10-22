import type { ProfileDTO } from "../types/dto";

export const MIN_IMPORTANCE = 1;
export const MAX_IMPORTANCE = 10;
export const DEFAULT_IMPORTANCE = 5;

/** Clamp a user rating to the 1–10 importance scale. */
export function clampImportance(value: number): number {
  if (!Number.isFinite(value)) {
    return DEFAULT_IMPORTANCE;
  }
  return Math.max(MIN_IMPORTANCE, Math.min(MAX_IMPORTANCE, Math.round(value)));
}

/**
 * Build the UI's importance ratings from a saved profile.
 *
 * Legacy profiles used 0–100 percentages that summed to 100. They are detected
 * and converted proportionally to the 1–10 scale so existing plans still load.
 */
export function importanceFromProfile(
  weights: Array<{ criterionId: string; weightValue: number }>,
  criterionIds: string[],
): Record<string, number> {
  const configured = new Map(
    weights.map((weight) => [weight.criterionId, weight.weightValue]),
  );
  const values = criterionIds.map(
    (criterionId) => configured.get(criterionId) ?? DEFAULT_IMPORTANCE,
  );
  const total = values.reduce((sum, value) => sum + Math.max(0, value), 0);
  const isLegacy =
    values.some((value) => value > MAX_IMPORTANCE) ||
    total > criterionIds.length * MAX_IMPORTANCE;

  const ratings: Record<string, number> = {};
  criterionIds.forEach((criterionId, index) => {
    const value = values[index];
    ratings[criterionId] = isLegacy && total > 0
      ? clampImportance((Math.max(0, value) / total) * MAX_IMPORTANCE)
      : clampImportance(value);
  });
  return ratings;
}

/** Normalise legacy 0–100 weights before persisting a profile. */
export function normalizeProfileWeights(profile: ProfileDTO): ProfileDTO {
  if (!profile.criteriaWeights || profile.criteriaWeights.length === 0) {
    return profile;
  }
  const criterionIds = profile.criteriaWeights.map((weight) => weight.criterionId);
  const ratings = importanceFromProfile(profile.criteriaWeights, criterionIds);
  return {
    ...profile,
    criteriaWeights: profile.criteriaWeights.map((weight) => ({
      ...weight,
      weightValue: ratings[weight.criterionId] ?? DEFAULT_IMPORTANCE,
    })),
  };
}
