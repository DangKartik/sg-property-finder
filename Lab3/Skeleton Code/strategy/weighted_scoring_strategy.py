from __future__ import annotations

from strategy.scoring_strategy import ScoringStrategy

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entity.preference_profile import PreferenceProfile
    from entity.subzone import Subzone


class WeightedScoringStrategy(ScoringStrategy):
    """«strategy» Scores a subzone as a weighted sum of criterion scores."""

    weightsMap: dict[str, float]  # private

    def __init__(self, weightsMap: dict[str, float]) -> None:
        """Create a WeightedScoringStrategy with its attributes (TODO: add validation if needed)."""
        self.weightsMap = weightsMap

    def calculateScore(self, subzone: Subzone, profile: PreferenceProfile) -> float:
        """Calculate score (public).

        Args:
            subzone: Subzone
            profile: PreferenceProfile
        Returns:
            float
        """
        raise NotImplementedError  # TODO
