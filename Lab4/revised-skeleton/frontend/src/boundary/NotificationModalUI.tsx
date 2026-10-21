/**
 * Stereotype: Boundary.
 * Reusable modal for validation errors, missing-data notices and API outages.
 */
export declare class NotificationModalUI {
  /** Modal heading. */
  modalTitle: string;

  /** Modal body text. */
  modalMessage: string;

  /**
   * Show the modal.
   * @param title Modal heading.
   * @param message Human-readable message.
   * @returns Nothing.
   */
  showModal(title: string, message: string): void;

  /**
   * Close the modal.
   * @returns Nothing.
   */
  closeModal(): void;
}
