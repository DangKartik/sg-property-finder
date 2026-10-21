import type { ReactNode } from "react";

export interface NotificationModalUIProps {
  title: string;
  message: string;
  onClose: () => void;
  children?: ReactNode;
}

/** Reusable modal for validation, missing-data and outage notices. */
export function NotificationModalUI({ title, message, onClose, children }: NotificationModalUIProps) {
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="modal notification-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="notification-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="modal-header">
          <h2 id="notification-title">{title}</h2>
          <button className="icon-button" onClick={onClose} aria-label="Close notification">
            ×
          </button>
        </header>
        <p className="modal-message">{message}</p>
        {children}
        <footer className="modal-footer">
          <button className="button primary" onClick={onClose}>
            Close
          </button>
        </footer>
      </section>
    </div>
  );
}
