import type { AddressSearchApi } from "../api/contracts";
import type { ProfileControl } from "../control/ProfileControl";
import type { AddressMatchDTO, ApiEnvelope, ProfileDTO } from "../types/dto";

/**
 * Stereotype: Boundary.
 * React form for creating or editing a preference profile, including criterion
 * weights and workplace-address verification.
 */
export declare class ProfileFormUI {
  /** Client-side profile controller backed by Dexie and backend validation. */
  profileControl: ProfileControl;

  /** OneMap-backed address search used to confirm the workplace anchor. */
  addressSearchApi: AddressSearchApi;

  /** Current form values. */
  currentProfileData: ProfileDTO;

  /** Criterion slider values keyed by criterion ID. */
  criteriaSliders: Map<string, number>;

  /**
   * Create the form with its required controllers.
   * @param profileControl Client-side profile controller.
   * @param addressSearchApi Address search API.
   */
  constructor(profileControl: ProfileControl, addressSearchApi: AddressSearchApi);

  /**
   * Render the form controls and current profile values.
   * @returns Nothing.
   */
  renderForm(): void;

  /**
   * Search for a workplace address so the user can confirm the match.
   * @param query Free-text address, building name or postal code.
   * @returns API envelope containing detailed address matches.
   * @throws When the API request fails or the response is malformed.
   */
  searchWorkplaceAddress(query: string): Promise<ApiEnvelope<AddressMatchDTO[]>>;

  /**
   * Apply a confirmed address match to the current profile.
   * @param match Confirmed address match.
   * @returns Nothing.
   */
  selectWorkplaceAddress(match: AddressMatchDTO): void;

  /**
   * Validate and submit the current profile for persistence.
   * @returns Nothing.
   * @throws When validation or persistence fails.
   */
  submitProfileData(): void;

  /**
   * Show a field-level validation error to the user.
   * @param message Human-readable validation message.
   * @returns Nothing.
   */
  displayValidationError(message: string): void;
}
