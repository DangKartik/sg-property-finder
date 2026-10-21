import type { ProfileDTO } from "../types/dto";

// Dexie/IndexedDB-backed profile store.
export declare class ProfileCatalog {
  profiles: Map<string, ProfileDTO>;

  addProfile(profile: ProfileDTO): Promise<void>;
  getProfile(profileId: string): Promise<ProfileDTO | undefined>;
  getAllProfiles(): Promise<ProfileDTO[]>;
  removeProfile(profileId: string): Promise<boolean>;
}
