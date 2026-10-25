import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import type { ProfileDTO } from "../types/dto";

export interface ProfileSelectorUIProps {
  profiles: ProfileDTO[];
  activeProfileId: string | null;
  busy?: boolean;
  onSelect: (profileId: string) => void;
  onEdit: (profileId: string) => void;
  onDelete: (profileId: string) => Promise<void> | void;
}

/** Compact top-right plan picker. Each plan row exposes its own Edit/Delete actions. */
export function ProfileSelectorUI({
  profiles,
  activeProfileId,
  busy = false,
  onSelect,
  onEdit,
  onDelete,
}: ProfileSelectorUIProps) {
  const [open, setOpen] = useState(false);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const deleteDisabled = profiles.length <= 1;
  const activeProfile = profiles.find((profile) => profile.profileId === activeProfileId);
  const profileToDelete = profiles.find((profile) => profile.profileId === confirmId);

  useEffect(() => {
    if (!open) {
      return;
    }
    function handleOutsideClick(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleOutsideClick);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [open]);

  return (
    <>
      <div className="plan-toolbar" ref={rootRef}>
        <span className="plan-toolbar-label">Plan</span>
        <div className="plan-picker">
          <button
            type="button"
            className="button small plan-picker-trigger"
            onClick={() => setOpen((current) => !current)}
            aria-haspopup="menu"
            aria-expanded={open}
            disabled={profiles.length === 0}
            title="Choose a preference plan"
          >
            <span className="plan-picker-name">
              {activeProfile?.profileName ?? (profiles.length === 0 ? "No saved plans" : "Select a plan")}
            </span>
            <span className="plan-picker-chevron" aria-hidden="true">
              ▾
            </span>
          </button>

          {open && (
            <div className="plan-menu" role="menu" aria-label="Preference plans">
              {profiles.map((profile) => {
                const profileId = profile.profileId ?? "";
                const isActive = profileId === activeProfileId;
                return (
                  <div
                    key={profileId || profile.profileName}
                    className={`plan-menu-row ${isActive ? "active" : ""}`}
                  >
                    <button
                      type="button"
                      className="plan-menu-select"
                      role="menuitemradio"
                      aria-checked={isActive}
                      onClick={() => {
                        onSelect(profileId);
                        setOpen(false);
                      }}
                      disabled={busy}
                    >
                      <span>{profile.profileName}</span>
                      {isActive && <span className="badge active">Active</span>}
                    </button>
                    <div className="plan-menu-actions">
                      <button
                        type="button"
                        className="link-button"
                        onClick={() => {
                          onEdit(profileId);
                          setOpen(false);
                        }}
                        disabled={busy || !profileId}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        className="link-button danger-text"
                        onClick={() => {
                          setConfirmId(profileId);
                          setOpen(false);
                        }}
                        disabled={deleteDisabled || busy || !profileId}
                        title={
                          deleteDisabled
                            ? "Keep at least one saved plan before deleting this one."
                            : `Delete ${profile.profileName}`
                        }
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                );
              })}
              {profiles.length === 0 && (
                <p className="muted plan-menu-empty">Create a plan to get started.</p>
              )}
            </div>
          )}
        </div>
      </div>

      {profileToDelete &&
        createPortal(
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
          </div>,
          document.body,
        )}
    </>
  );
}
