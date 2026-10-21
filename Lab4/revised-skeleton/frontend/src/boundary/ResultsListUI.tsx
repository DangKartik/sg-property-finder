import type { RankingApi } from "../api/contracts";
import type { RecommendationItemDTO, RecommendationSetDTO } from "../types/dto";

/**
 * Stereotype: Boundary.
 * Ranked results sidebar; clicking a card highlights the matching map polygon.
 */
export declare class ResultsListUI {
  /** Ranking API used to regenerate recommendations. */
  rankingApi: RankingApi;

  /** Recommendations currently rendered in the sidebar. */
  displayedRecommendations: RecommendationItemDTO[];

  /**
   * Create the results list with its ranking dependency.
   * @param rankingApi Ranking API.
   */
  constructor(rankingApi: RankingApi);

  /**
   * Render a recommendation set, ordered by rank.
   * @param results Recommendation set returned by the backend.
   * @returns Nothing.
   */
  renderResults(results: RecommendationSetDTO): void;

  /**
   * Handle a subzone card click.
   * @param subzoneId Subzone code.
   * @returns Nothing.
   */
  onSubzoneClick(subzoneId: string): void;
}
