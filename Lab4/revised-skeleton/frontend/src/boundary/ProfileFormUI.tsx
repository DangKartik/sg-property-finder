import type { AddressSearchApi } from "../api/contracts";
import type { ProfileControl } from "../control/ProfileControl";
import type { AddressMatchDTO, ApiEnvelope, ProfileDTO } from "../types/dto";

// React component; implementation deferred.
export declare class ProfileFormUI {
  profileControl: ProfileControl;
  addressSearchApi: AddressSearchApi;
  currentProfileData: ProfileDTO;
  criteriaSliders: Map<string, number>;

  constructor(profileControl: ProfileControl, addressSearchApi: AddressSearchApi);

  renderForm(): void;
  searchWorkplaceAddress(query: string): Promise<ApiEnvelope<AddressMatchDTO[]>>;
  selectWorkplaceAddress(match: AddressMatchDTO): void;
  submitProfileData(): void;
  displayValidationError(message: string): void;
}
