from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.container.subzone_registry import SubzoneRegistry
    from app.control.commute_control import CommuteControl
    from app.entity.preference_profile import PreferenceProfile
    from app.entity.recommendation_set import RecommendationSet
    from app.strategy.scoring_strategy import ScoringStrategy


class RankingControl:
    subzoneRegistry: SubzoneRegistry
    scoringStrategy: ScoringStrategy
    commuteControl: CommuteControl

    def __init__(
        self,
        subzoneRegistry: SubzoneRegistry,
        scoringStrategy: ScoringStrategy,
        commuteControl: CommuteControl,
    ) -> None: ...
    def calculateScore(self, profile: PreferenceProfile, subzoneCode: str) -> float: ...
    def generateRankedRecommendations(self, profile: PreferenceProfile) -> RecommendationSet: ...
