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
import { rescaleWeights, round1 } from "../utils/weights";

const FLAT_TYPES = [
  "1 ROOM",
  "2 ROOM",
  "3 ROOM",
  "4 ROOM",
  "5 ROOM",
  "EXECUTIVE",
  "MULTI-GENERATION",
];

export interface ProfileFormUIProps {
  profileControl: ProfileControl;
  addressSearchApi: AddressSearchApi;
  criteria: CriterionDefinitionDTO[];
  initialProfile?: ProfileDTO | null;
  onSaved: (profileId: string) => void | Promise<void>;
  onCancel: () => void;
  onNotify: (title: string, message: string) => void;
}

/** Preference form with budget, flat types, auto-rescaling weights and address verification. */
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
    const next: Record<string, number> = {};
    if (configured.length > 0) {
      criterionIds.forEach((id) => {
        next[id] = configured.find((weight) => weight.criterionId === id)?.weightValue ?? 0;
      });
    } else {
      const equal = round1(100 / criterionIds.length);
      criterionIds.forEach((id, index) => {
        next[id] = index === criterionIds.length - 1
          ? round1(100 - equal * (criterionIds.length - 1))
          : equal;
      });
    }
    setWeights(next);
  }, [criterionIds, initialProfile]);

  const totalWeight = round1(
    criterionIds.reduce((sum, id) => sum + (weights[id] ?? 0), 0),
  );

  function handleWeightChange(id: string, value: number) {
    setWeights((current) => rescaleWeights(current, id, value, criterionIds));
  }

  function toggleFlatType(flatType: string) {
    setFlatTypes((current) =>
      current.includes(flatType)
        ? current.filter((item) => item !== flatType)
        : [...current, flatType],
    );
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
    if (Math.abs(totalWeight - 100) > 0.05) {
      setErrors(["Criteria weights must total 100%."]);
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
        weightValue: round1(weights[criterionId] ?? 0),
      })),
      preferredCommuteMode: commuteMode,
      departureTime: null,
      isActive: true,
      creationTime: initialProfile?.creationTime ?? new Date().toISOString(),
      lastUpdatedTime: new Date().toISOString(),
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
          Criteria weights <span className={Math.abs(totalWeight - 100) > 0.05 ? "error-text" : "muted"}>
            ({totalWeight.toFixed(1)}%)
          </span>
        </legend>
        {criteria.map((criterion) => (
          <label className="weight-row" key={criterion.criterionId}>
            <span className="weight-label">
              {criterion.criterionName}
              <small>{criterion.unit}</small>
            </span>
            <input
              type="range"
              min={0}
              max={100}
              step={1}
              value={weights[criterion.criterionId] ?? 0}
              onChange={(event) =>
                handleWeightChange(criterion.criterionId, Number(event.target.value))
              }
            />
            <output>{(weights[criterion.criterionId] ?? 0).toFixed(1)}%</output>
          </label>
        ))}
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
