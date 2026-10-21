import type { ComparisonApi } from "../api/contracts";
import type { ComparisonResultDTO } from "../types/dto";

/**
 * Stereotype: Boundary.
 * Side-by-side comparison matrix for two or more selected subzones.
 */
export declare class ComparisonUI {
  /** Comparison API. */
  comparisonApi: ComparisonApi;

  /** Subzone codes currently selected for comparison. */
  selectedSubzoneIds: string[];

  /** Latest comparison result, or `null` before comparison. */
  comparisonResult: ComparisonResultDTO | null;

  /**
   * Create the comparison view with its API.
   * @param comparisonApi Comparison API.
   */
  constructor(comparisonApi: ComparisonApi);

  /**
   * Render the comparison matrix.
   * @param result Comparison result including full factsheets.
   * @returns Nothing.
   */
  renderComparison(result: ComparisonResultDTO): void;

  /**
   * Add a subzone to the comparison selection.
   * @param subzoneId Subzone code.
   * @returns Nothing.
   */
  addToComparison(subzoneId: string): void;

  /**
   * Remove a subzone from the comparison selection.
   * @param subzoneId Subzone code.
   * @returns Nothing.
   */
  removeFromComparison(subzoneId: string): void;

  /**
   * Handle a comparison card click.
   * @param subzoneId Subzone code.
   * @returns Nothing.
   */
  onSubzoneClick(subzoneId: string): void;
}
