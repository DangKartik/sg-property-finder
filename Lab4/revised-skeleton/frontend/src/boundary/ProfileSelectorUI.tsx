import type { RankingApi } from "../api/contracts";
import type { ProfileDTO } from "../types/dto";

// React component; implementation deferred.
export declare class ProfileSelectorUI {
  rankingApi: RankingApi;
  profileDropdownList: string[];

  constructor(rankingApi: RankingApi);

  renderDropdown(profiles: ProfileDTO[]): void;
  onProfileSelected(profileId: string): void;
}
