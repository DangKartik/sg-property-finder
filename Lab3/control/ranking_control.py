from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.control.commute_control import CommuteControl
    from sgpropfinder.container.profile_catalog import ProfileCatalog
    from sgpropfinder.entity.recommendation_set import RecommendationSet
    from sgpropfinder.strategy.scoring_strategy import ScoringStrategy
    from sgpropfinder.container.subzone_registry import SubzoneRegistry


class RankingControl:
    """«control»"""

    profileCatalog: ProfileCatalog
    subzoneRegistry: SubzoneRegistry
    scoringStrategy: ScoringStrategy
    commuteControl: CommuteControl

    def selectProfile(self, profileId: str) -> None:
        raise NotImplementedError  # TODO

    def calculateScore(self, profileId: str, subzoneCode: str) -> float:
        raise NotImplementedError  # TODO

    def generateRankedRecommendations(self, profileId: str) -> RecommendationSet:
        raise NotImplementedError  # TODO
