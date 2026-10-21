import type { ProfileValidationApi } from "../api/contracts";
import type { ProfileCatalog } from "../container/ProfileCatalog";
import type { ProfileDTO } from "../types/dto";

export declare class ProfileControl {
  profileCatalog: ProfileCatalog;
  validator: ProfileValidationApi;

  constructor(profileCatalog: ProfileCatalog, validator: ProfileValidationApi);

  createProfile(data: ProfileDTO): Promise<string>;
  updateProfile(profileId: string, data: ProfileDTO): Promise<boolean>;
  deleteProfile(profileId: string): Promise<boolean>;
}
