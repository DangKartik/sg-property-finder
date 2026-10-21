import type { ProfileDTO } from "../types/dto";

/**
 * Stereotype: Container.
 * Dexie/IndexedDB-backed repository for local preference profiles.
 *
 * The browser is the source of truth for profiles; the backend is stateless.
 */
export declare class ProfileCatalog {
  /** In-memory view of the profiles currently loaded from IndexedDB. */
  profiles: Map<string, ProfileDTO>;

  /**
   * Persist a new profile.
   * @param profile Profile to save.
   * @returns Resolves when the write completes.
   * @throws When the IndexedDB transaction fails.
   */
  addProfile(profile: ProfileDTO): Promise<void>;

  /**
   * Load one profile.
   * @param profileId Profile identifier.
   * @returns The profile, or `undefined` when it does not exist.
   * @throws When the IndexedDB read fails.
   */
  getProfile(profileId: string): Promise<ProfileDTO | undefined>;

  /**
   * Load all saved profiles.
   * @returns All profiles in the local store.
   * @throws When the IndexedDB read fails.
   */
  getAllProfiles(): Promise<ProfileDTO[]>;

  /**
   * Delete a profile.
   * @param profileId Profile identifier.
   * @returns `true` when a profile was deleted, otherwise `false`.
   * @throws When the IndexedDB transaction fails.
   */
  removeProfile(profileId: string): Promise<boolean>;
}
