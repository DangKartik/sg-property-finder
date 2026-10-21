import { useState } from "react";
import type { ProfileDTO } from "../types/dto";

export interface ProfileSelectorUIProps {
  profiles: ProfileDTO[];
  activeProfileId: string | null;
  busy?: boolean;
  onSelect: (profileId: string) => void;
  onCreate: () => void;
  onDelete: (profileId: string) => Promise<void> | void;
}

/** Saved-plan dropdown with active badge and delete confirmation. */
export function ProfileSelectorUI({
  profiles,
  activeProfileId,
  busy = false,
  onSelect,
  onCreate,
  onDelete,
}: ProfileSelectorUIProps) {
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const deleteDisabled = profiles.length <= 1;
  const profileToDelete = profiles.find((profile) => profile.profileId === confirmId);

  return (
    <section className="panel plan-selector">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Preference plans</p>
          <h2>Saved plans</h2>
        </div>
        <button className="button small primary" onClick={onCreate} disabled={busy}>
          + New plan
        </button>
      </div>

      {profiles.length === 0 ? (
        <p className="muted">No saved plans yet. Create one to get recommendations.</p>
      ) : (
        <div className="plan-row">
          <label className="sr-only" htmlFor="profile-select">
            Select a preference plan
          </label>
          <select
            id="profile-select"
            value={activeProfileId ?? ""}
            onChange={(event) => onSelect(event.target.value)}
            disabled={busy}
          >
            <option value="" disabled>
              Select a plan
            </option>
            {profiles.map((profile) => (
              <option key={profile.profileId} value={profile.profileId ?? ""}>
                {profile.profileName}
              </option>
            ))}
          </select>
          {activeProfileId && <span className="badge active">Active</span>}
          <button
            className="button small danger-ghost"
            disabled={deleteDisabled || busy || !activeProfileId}
            title={
              deleteDisabled
                ? "Keep at least one saved plan. Create another plan before deleting this one."
                : "Delete the selected plan"
            }
            onClick={() => activeProfileId && setConfirmId(activeProfileId)}
          >
            Delete
          </button>
        </div>
      )}

      {deleteDisabled && profiles.length === 1 && (
        <p className="hint">At least one plan must remain. Create another plan to enable deletion.</p>
      )}

      {profileToDelete && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setConfirmId(null)}>
          <section
            className="modal compact-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-plan-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <header className="modal-header">
              <h2 id="delete-plan-title">Delete “{profileToDelete.profileName}”?</h2>
              <button className="icon-button" onClick={() => setConfirmId(null)} aria-label="Cancel delete">
                ×
              </button>
            </header>
            <p>This removes the plan from this browser's IndexedDB. It cannot be undone.</p>
            <footer className="modal-footer">
              <button className="button" onClick={() => setConfirmId(null)}>
                Cancel
              </button>
              <button
                className="button danger"
                onClick={async () => {
                  if (confirmId) {
                    await onDelete(confirmId);
                    setConfirmId(null);
                  }
                }}
              >
                Delete plan
              </button>
            </footer>
          </section>
        </div>
      )}
    </section>
  );
}
