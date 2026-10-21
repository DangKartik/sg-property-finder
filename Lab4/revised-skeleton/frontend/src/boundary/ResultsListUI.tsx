import type { RankingApi } from "../api/contracts";
import type { RecommendationItemDTO, RecommendationSetDTO } from "../types/dto";

// React component; implementation deferred.
export declare class ResultsListUI {
  rankingApi: RankingApi;
  displayedRecommendations: RecommendationItemDTO[];

  constructor(rankingApi: RankingApi);

  renderResults(results: RecommendationSetDTO): void;
  onSubzoneClick(subzoneId: string): void;
}
