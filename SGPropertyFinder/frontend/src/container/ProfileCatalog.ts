import Dexie, { type Table } from "dexie";
import type { ProfileDTO } from "../types/dto";
import { normalizeProfileWeights } from "../utils/weights";

class ProfileDatabase extends Dexie {
  profiles!: Table<ProfileDTO, string>;

  constructor() {
    super("sgpropfinder");
    this.version(1).stores({
      profiles: "profileId, profileName, lastUpdatedTime",
    });
  }
}

/**
 * Stereotype: Container.
 * Dexie/IndexedDB repository for local preference profiles.
 */
export class ProfileCatalog {
  profiles = new Map<string, ProfileDTO>();
  private readonly db = new ProfileDatabase();

  async saveToLocalStorage(profile: ProfileDTO): Promise<string> {
    const profileId = profile.profileId ?? makeId();
    const record = normalizeProfileWeights({
      ...profile,
      profileId,
      lastUpdatedTime: new Date().toISOString(),
      creationTime: profile.creationTime ?? new Date().toISOString(),
    });
    await this.db.profiles.put(record);
    this.profiles.set(profileId, record);
    return profileId;
  }

  async loadFromLocalStorage(): Promise<ProfileDTO[]> {
    const stored = await this.db.profiles.toArray();
    const profiles = stored.map(normalizeProfileWeights);
    const migrated = profiles.filter(
      (profile, index) =>
        JSON.stringify(profile.criteriaWeights) !==
        JSON.stringify(stored[index].criteriaWeights),
    );
    if (migrated.length > 0) {
      await this.db.profiles.bulkPut(migrated);
    }
    this.profiles = new Map(profiles.map((profile) => [profile.profileId as string, profile]));
    return profiles.sort((a, b) => (a.creationTime ?? "").localeCompare(b.creationTime ?? ""));
  }

  async deleteProfile(profileId: string): Promise<boolean> {
    await this.db.profiles.delete(profileId);
    return this.profiles.delete(profileId);
  }

  async addProfile(profile: ProfileDTO): Promise<void> {
    await this.saveToLocalStorage(profile);
  }

  async getProfile(profileId: string): Promise<ProfileDTO | undefined> {
    return this.profiles.get(profileId) ?? (await this.db.profiles.get(profileId));
  }

  async getAllProfiles(): Promise<ProfileDTO[]> {
    return this.loadFromLocalStorage();
  }

  async removeProfile(profileId: string): Promise<boolean> {
    return this.deleteProfile(profileId);
  }
}

function makeId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `profile-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
