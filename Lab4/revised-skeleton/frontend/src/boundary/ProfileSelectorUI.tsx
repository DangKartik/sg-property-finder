import type { RankingApi } from "../api/contracts";
import type { ProfileDTO } from "../types/dto";

/**
 * Stereotype: Boundary.
 * Dropdown for selecting a saved preference profile and triggering a ranking.
 */
export declare class ProfileSelectorUI {
  /** Ranking API used when a profile is selected. */
  rankingApi: RankingApi;

  /** Display labels for the saved profiles. */
  profileDropdownList: string[];

  /**
   * Create the selector with its ranking dependency.
   * @param rankingApi Ranking API.
   */
  constructor(rankingApi: RankingApi);

  /**
   * Render the dropdown from saved profiles.
   * @param profiles Profiles loaded from Dexie.
   * @returns Nothing.
   */
  renderDropdown(profiles: ProfileDTO[]): void;

  /**
   * Handle a profile selection and start ranking.
   * @param profileId Selected profile identifier.
   * @returns Nothing.
   * @throws When the ranking request fails.
   */
  onProfileSelected(profileId: string): void;
}
