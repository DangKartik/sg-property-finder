import type { ProfileValidationApi } from "../api/contracts";
import type { ProfileCatalog } from "../container/ProfileCatalog";
import type { ProfileDTO, ValidationErrorDTO } from "../types/dto";

export class ProfileValidationError extends Error {
  readonly errors: ValidationErrorDTO[];

  constructor(errors: ValidationErrorDTO[]) {
    super(errors.map((error) => error.message).join(" "));
    this.name = "ProfileValidationError";
    this.errors = errors;
  }
}

/**
 * Stereotype: Control.
 * Client-side profile CRUD controller. The backend is the authoritative
 * validator; Dexie/IndexedDB is the local source of truth.
 */
export class ProfileControl {
  constructor(
    public readonly profileCatalog: ProfileCatalog,
    public readonly validator: ProfileValidationApi,
  ) {}

  async createProfile(data: ProfileDTO): Promise<string> {
    await this.validate(data);
    return this.profileCatalog.saveToLocalStorage({
      ...data,
      profileId: data.profileId ?? makeId(),
      creationTime: data.creationTime ?? new Date().toISOString(),
    });
  }

  async updateProfile(profileId: string, data: ProfileDTO): Promise<boolean> {
    await this.validate(data);
    await this.profileCatalog.saveToLocalStorage({
      ...data,
      profileId,
      creationTime: data.creationTime ?? new Date().toISOString(),
    });
    return true;
  }

  async deleteProfile(profileId: string): Promise<boolean> {
    return this.profileCatalog.deleteProfile(profileId);
  }

  async activateProfile(profileId: string): Promise<void> {
    await this.profileCatalog.markActive(profileId);
  }

  private async validate(data: ProfileDTO): Promise<void> {
    const envelope = await this.validator.validateProfileData(data);
    if (!envelope.success || !envelope.data) {
      throw new ProfileValidationError([
        {
          field: "profile",
          message: envelope.error?.message ?? "Unable to validate this profile.",
        },
      ]);
    }
    if (!envelope.data.isValid) {
      throw new ProfileValidationError(envelope.data.errors);
    }
  }
}

function makeId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `profile-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
