import type { ProfileValidationApi } from "../api/contracts";
import type { ProfileCatalog } from "../container/ProfileCatalog";
import type { ProfileDTO } from "../types/dto";

/**
 * Stereotype: Control.
 * Client-side profile CRUD controller. It validates through the backend and
 * persists to Dexie/IndexedDB.
 */
export declare class ProfileControl {
  /** Local profile repository. */
  profileCatalog: ProfileCatalog;

  /** Authoritative profile validation API. */
  validator: ProfileValidationApi;

  /**
   * Create the controller with its catalog and validator.
   * @param profileCatalog Local profile repository.
   * @param validator Backend validation API.
   */
  constructor(profileCatalog: ProfileCatalog, validator: ProfileValidationApi);

  /**
   * Validate and create a profile.
   * @param data Profile input.
   * @returns The new profile identifier.
   * @throws When validation fails or persistence fails.
   */
  createProfile(data: ProfileDTO): Promise<string>;

  /**
   * Validate and update a profile.
   * @param profileId Existing profile identifier.
   * @param data Updated profile input.
   * @returns `true` when the update succeeds, otherwise `false`.
   * @throws When validation or persistence fails.
   */
  updateProfile(profileId: string, data: ProfileDTO): Promise<boolean>;

  /**
   * Delete a profile.
   * @param profileId Profile identifier.
   * @returns `true` when a profile was deleted, otherwise `false`.
   * @throws When the IndexedDB transaction fails.
   */
  deleteProfile(profileId: string): Promise<boolean>;
}
