import { useEffect, useMemo, useState } from "react";
import type { AddressSearchApi } from "../api/contracts";
import type { ProfileControl } from "../control/ProfileControl";
import { ProfileValidationError } from "../control/ProfileControl";
import type {
  AddressMatchDTO,
  CoordinatesDTO,
  CriterionDefinitionDTO,
  ProfileDTO,
  TransitModeDTO,
} from "../types/dto";
import {
  DEFAULT_IMPORTANCE,
  clampImportance,
  importanceFromProfile,
} from "../utils/weights";

const FLAT_TYPES = [
  "1 ROOM",
  "2 ROOM",
  "3 ROOM",
  "4 ROOM",
  "5 ROOM",
  "EXECUTIVE",
  "MULTI-GENERATION",
];

type MinimumKey =
  | "minimumPrimarySchools"
  | "minimumSecondarySchools"
  | "minimumTertiarySchools"
  | "minimumMalls"
  | "minimumHospitals";

const MINIMUM_FIELDS: Array<{ key: MinimumKey; label: string; radius: string }> = [
  { key: "minimumPrimarySchools", label: "Primary schools", radius: "within 1 km" },
  { key: "minimumSecondarySchools", label: "Secondary schools", radius: "within 1 km" },
  { key: "minimumTertiarySchools", label: "Tertiary schools (JC/university)", radius: "within 1 km" },
  { key: "minimumMalls", label: "Malls", radius: "within 1 km" },
  { key: "minimumHospitals", label: "Hospitals", radius: "within 2 km" },
];

const MAX_MINIMUM_COUNT = 50;

export interface ProfileFormUIProps {
  profileControl: ProfileControl;
  addressSearchApi: AddressSearchApi;
  criteria: CriterionDefinitionDTO[];
  initialProfile?: ProfileDTO | null;
  onSaved: (profileId: string) => void | Promise<void>;
  onCancel: () => void;
  onNotify: (title: string, message: string) => void;
}

/** Preference form with budget, flat types, 1–10 importance ratings and address verification. */
export function ProfileFormUI({
  profileControl,
  addressSearchApi,
  criteria,
  initialProfile,
  onSaved,
  onCancel,
  onNotify,
}: ProfileFormUIProps) {
  const [profileName, setProfileName] = useState(initialProfile?.profileName ?? "My Plan");
  const [budgetMin, setBudgetMin] = useState(initialProfile?.budgetMin ?? 0);
  const [budgetMax, setBudgetMax] = useState(initialProfile?.budgetMax ?? 600_000);
  const [flatTypes, setFlatTypes] = useState<string[]>(
    initialProfile?.selectedFlatTypes ?? ["4 ROOM"],
  );
  const [weights, setWeights] = useState<Record<string, number>>({});
  const [workplaceAddress, setWorkplaceAddress] = useState(
    initialProfile?.workplaceAddress ?? "",
  );
  const [anchor, setAnchor] = useState<CoordinatesDTO | null>(
    initialProfile?.anchorCoordinates ?? null,
  );
  const [addressQuery, setAddressQuery] = useState(initialProfile?.workplaceAddress ?? "");
  const [matches, setMatches] = useState<AddressMatchDTO[]>([]);
  const [searching, setSearching] = useState(false);
  const [commuteMode, setCommuteMode] = useState<TransitModeDTO>(
    initialProfile?.preferredCommuteMode ?? "PUBLIC_TRANSIT",
  );
  const [minimums, setMinimums] = useState<Record<MinimumKey, number>>({
    minimumPrimarySchools: initialProfile?.minimumPrimarySchools ?? 0,
    minimumSecondarySchools: initialProfile?.minimumSecondarySchools ?? 0,
    minimumTertiarySchools: initialProfile?.minimumTertiarySchools ?? 0,
    minimumMalls: initialProfile?.minimumMalls ?? 0,
    minimumHospitals: initialProfile?.minimumHospitals ?? 0,
  });
  const [errors, setErrors] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  const criterionIds = useMemo(
    () => criteria.map((criterion) => criterion.criterionId),
    [criteria],
  );

  useEffect(() => {
    if (criterionIds.length === 0) {
      return;
    }
    const configured = initialProfile?.criteriaWeights ?? [];
    setWeights(importanceFromProfile(configured, criterionIds));
  }, [criterionIds, initialProfile]);

  function handleWeightChange(id: string, value: number) {
    setWeights((current) => ({
      ...current,
      [id]: clampImportance(value),
    }));
  }

  function toggleFlatType(flatType: string) {
    setFlatTypes((current) =>
      current.includes(flatType)
        ? current.filter((item) => item !== flatType)
        : [...current, flatType],
    );
  }

  function updateMinimum(key: MinimumKey, value: string) {
    const numeric = Number(value);
    const next = Number.isFinite(numeric)
      ? Math.max(0, Math.min(MAX_MINIMUM_COUNT, Math.round(numeric)))
      : 0;
    setMinimums((current) => ({ ...current, [key]: next }));
  }

  async function searchAddress() {
    const query = addressQuery.trim();
    if (!query) {
      onNotify("Enter a workplace address", "Enter a postal code, building name or street address.");
      return;
    }
    setSearching(true);
    setErrors([]);
    try {
      const envelope = await addressSearchApi.searchAddress(query);
      if (!envelope.success || !envelope.data) {
        onNotify("Address search failed", envelope.error?.message ?? "Unable to search for this address.");
        setMatches([]);
        return;
      }
      if (envelope.data.length === 0) {
        onNotify("Address not found", "Try a postal code or a more specific building name.");
      }
      setMatches(envelope.data);
    } catch (error) {
      onNotify("Address search failed", error instanceof Error ? error.message : "Try again.");
    } finally {
      setSearching(false);
    }
  }

  function selectAddress(match: AddressMatchDTO) {
    setWorkplaceAddress(match.formattedAddress);
    setAddressQuery(match.formattedAddress);
    setAnchor(match.coordinates);
    setMatches([]);
  }

  async function submitProfile() {
    if (!anchor) {
      setErrors(["Search for and select a workplace address before saving."]);
      return;
    }
    if (flatTypes.length === 0) {
      setErrors(["Select at least one flat type to continue."]);
      return;
    }
    if (
      criterionIds.some((criterionId) => {
        const rating = weights[criterionId] ?? DEFAULT_IMPORTANCE;
        return rating < 1 || rating > 10;
      })
    ) {
      setErrors(["Each criterion importance must be between 1 and 10."]);
      return;
    }
    if (
      MINIMUM_FIELDS.some(({ key }) => {
        const value = minimums[key];
        return !Number.isInteger(value) || value < 0 || value > MAX_MINIMUM_COUNT;
      })
    ) {
      setErrors([
        `Minimum counts must be whole numbers between 0 and ${MAX_MINIMUM_COUNT}.`,
      ]);
      return;
    }

    const data: ProfileDTO = {
      profileId: initialProfile?.profileId ?? null,
      profileName: profileName.trim() || "My Plan",
      budgetMin,
      budgetMax,
      selectedFlatTypes: flatTypes,
      workplaceAddress,
      anchorCoordinates: anchor,
      criteriaWeights: criterionIds.map((criterionId) => ({
        criterionId,
        weightValue: clampImportance(weights[criterionId] ?? DEFAULT_IMPORTANCE),
      })),
      preferredCommuteMode: commuteMode,
      departureTime: null,
      isActive: true,
      creationTime: initialProfile?.creationTime ?? new Date().toISOString(),
      lastUpdatedTime: new Date().toISOString(),
      minimumPrimarySchools: minimums.minimumPrimarySchools,
      minimumSecondarySchools: minimums.minimumSecondarySchools,
      minimumTertiarySchools: minimums.minimumTertiarySchools,
      minimumMalls: minimums.minimumMalls,
      minimumHospitals: minimums.minimumHospitals,
    };

    setSaving(true);
    setErrors([]);
    try {
      const profileId = initialProfile?.profileId
        ? await profileControl.updateProfile(initialProfile.profileId, data).then(
            (updated) => (updated ? initialProfile.profileId as string : ""),
          )
        : await profileControl.createProfile(data);
      if (!profileId) {
        throw new Error("The profile could not be saved.");
      }
      await onSaved(profileId);
    } catch (error) {
      if (error instanceof ProfileValidationError) {
        setErrors(error.errors.map((fieldError) => fieldError.message));
      } else {
        onNotify("Could not save plan", error instanceof Error ? error.message : "Try again.");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="panel profile-form">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">{initialProfile ? "Edit plan" : "New plan"}</p>
          <h2>What matters to you?</h2>
        </div>
        <button className="icon-button" onClick={onCancel} aria-label="Close profile form">
          ×
        </button>
      </div>

      {errors.length > 0 && (
        <div className="form-errors" role="alert">
          {errors.map((message) => (
            <p key={message}>{message}</p>
          ))}
        </div>
      )}

      <label className="field">
        <span>Plan name</span>
        <input value={profileName} onChange={(event) => setProfileName(event.target.value)} maxLength={60} />
      </label>

      <fieldset className="field-group">
        <legend>Budget (SGD)</legend>
        <div className="budget-readout">
          <strong>{formatBudget(budgetMin)}</strong>
          <span>to</span>
          <strong>{formatBudget(budgetMax)}</strong>
        </div>
        <label className="range-label">
          Minimum
          <input
            type="range"
            min={0}
            max={1_500_000}
            step={10_000}
            value={budgetMin}
            onChange={(event) => {
              const value = Number(event.target.value);
              setBudgetMin(Math.min(value, budgetMax - 10_000));
            }}
          />
        </label>
        <label className="range-label">
          Maximum
          <input
            type="range"
            min={0}
            max={1_500_000}
            step={10_000}
            value={budgetMax}
            onChange={(event) => {
              const value = Number(event.target.value);
              setBudgetMax(Math.max(value, budgetMin + 10_000));
            }}
          />
        </label>
      </fieldset>

      <fieldset className="field-group">
        <legend>Flat types</legend>
        <div className="checkbox-grid">
          {FLAT_TYPES.map((flatType) => (
            <label key={flatType} className="check-label">
              <input
                type="checkbox"
                checked={flatTypes.includes(flatType)}
                onChange={() => toggleFlatType(flatType)}
              />
              {flatType}
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset className="field-group">
        <legend>Workplace / CBD anchor</legend>
        <div className="address-search-row">
          <input
            value={addressQuery}
            onChange={(event) => {
              setAddressQuery(event.target.value);
              if (event.target.value !== workplaceAddress) {
                setAnchor(null);
              }
            }}
            placeholder="Postal code, building or street"
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                void searchAddress();
              }
            }}
          />
          <button className="button" onClick={() => void searchAddress()} disabled={searching}>
            {searching ? "Searching…" : "Search"}
          </button>
        </div>
        {workplaceAddress && anchor && (
          <p className="confirmed-address">
            ✓ {workplaceAddress}{" "}
            <span className="muted">({anchor.latitude.toFixed(4)}, {anchor.longitude.toFixed(4)})</span>
          </p>
        )}
        {matches.length > 0 && (
          <div className="address-matches" role="listbox" aria-label="Address matches">
            {matches.map((match) => (
              <button
                key={`${match.postalCode}-${match.formattedAddress}`}
                className="address-match"
                onClick={() => selectAddress(match)}
              >
                <span>{match.formattedAddress}</span>
                <small>
                  {match.postalCode}
                  {match.confidenceScore !== null
                    ? ` · ${Math.round(match.confidenceScore * 100)}% match`
                    : ""}
                </small>
              </button>
            ))}
          </div>
        )}
        <label className="field">
          <span>Commute mode</span>
          <select
            value={commuteMode}
            onChange={(event) => setCommuteMode(event.target.value as TransitModeDTO)}
          >
            <option value="PUBLIC_TRANSIT">Public transport</option>
            <option value="DRIVING">Driving</option>
            <option value="WALKING">Walking</option>
          </select>
        </label>
      </fieldset>

      <fieldset className="field-group">
        <legend>
          Hard minimums <span className="muted">(subzones below any value are discarded)</span>
        </legend>
        <div className="minimum-grid">
          {MINIMUM_FIELDS.map(({ key, label, radius }) => (
            <label className="minimum-field" key={key}>
              <span>
                {label}
                <small>{radius}</small>
              </span>
              <input
                type="number"
                min={0}
                max={MAX_MINIMUM_COUNT}
                step={1}
                value={minimums[key]}
                onChange={(event) => updateMinimum(key, event.target.value)}
              />
            </label>
          ))}
        </div>
        <p className="hint">
          Set a value to 0 for no requirement. These are hard filters: a subzone
          that does not meet every minimum is removed before scoring.
        </p>
      </fieldset>

      <fieldset className="field-group">
        <legend>
          Criteria importance <span className="muted">(1 = not important, 10 = very important)</span>
        </legend>
        {criteria.map((criterion) => {
          const rating = weights[criterion.criterionId] ?? DEFAULT_IMPORTANCE;
          return (
            <label className="weight-row" key={criterion.criterionId}>
              <span className="weight-label">
                {criterion.criterionName}
                <small>{criterion.unit}</small>
              </span>
              <input
                type="range"
                min={1}
                max={10}
                step={1}
                value={rating}
                onChange={(event) =>
                  handleWeightChange(criterion.criterionId, Number(event.target.value))
                }
              />
              <output>{rating}/10</output>
            </label>
          );
        })}
        <p className="hint">
          Ratings are relative. The scoring engine normalises them into weights
          that sum to 1.0, so there is no need to make them add up to 100%.
        </p>
      </fieldset>

      <div className="form-actions">
        <button className="button" onClick={onCancel} disabled={saving}>
          Cancel
        </button>
        <button className="button primary" onClick={() => void submitProfile()} disabled={saving}>
          {saving ? "Saving…" : "Save & rank"}
        </button>
      </div>
    </section>
  );
}

function formatBudget(value: number): string {
  return new Intl.NumberFormat("en-SG", {
    style: "currency",
    currency: "SGD",
    maximumFractionDigits: 0,
  }).format(value);
}
