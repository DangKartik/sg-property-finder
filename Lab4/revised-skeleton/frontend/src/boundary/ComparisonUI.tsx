import type { ComparisonApi } from "../api/contracts";
import type { ComparisonResultDTO } from "../types/dto";

// React component added for FR12 (compare neighbourhoods); implementation deferred.
export declare class ComparisonUI {
  comparisonApi: ComparisonApi;
  selectedSubzoneIds: string[];
  comparisonResult: ComparisonResultDTO | null;

  constructor(comparisonApi: ComparisonApi);

  renderComparison(result: ComparisonResultDTO): void;
  addToComparison(subzoneId: string): void;
  removeFromComparison(subzoneId: string): void;
  onSubzoneClick(subzoneId: string): void;
}
