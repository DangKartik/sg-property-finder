"""Recommendation ranking control."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.core.serialization import toJsonable
from app.core.time import CBD_LATITUDE, CBD_LONGITUDE, nextWeekdayPeak
from app.entity.enums import TransitMode
from app.entity.types import Coordinates

if TYPE_CHECKING:
    from app.container.subzone_registry import SubzoneRegistry
    from app.control.commute_control import CommuteControl
    from app.control.data_availability_notifier import DataAvailabilityNotifier
    from app.entity.commute_estimate import CommuteEstimate
    from app.entity.preference_profile import PreferenceProfile
    from app.entity.recommendation_set import RecommendationSet
    from app.strategy.scoring_strategy import ScoringStrategy


class RankingControl:
    """Stereotype: Control. Coordinates scoring and ranking for one profile."""

    def __init__(
        self,
        subzoneRegistry: SubzoneRegistry,
        scoringStrategy: ScoringStrategy,
        commuteControl: CommuteControl,
        notifier: DataAvailabilityNotifier | None = None,
        dataSnapshotId: str = "LOCAL",
        dataAsOf: datetime | None = None,
    ) -> None:
        """Store the ranking dependencies and snapshot identity."""
        self.subzoneRegistry = subzoneRegistry
        self.scoringStrategy = scoringStrategy
        self.commuteControl = commuteControl
        self.notifier = notifier
        self.dataSnapshotId = dataSnapshotId
        self.dataAsOf = dataAsOf or datetime.now(timezone.utc)

    def calculateScore(self, profile: PreferenceProfile, subzoneCode: str) -> float:
        """Calculate one subzone's score using the configured strategy."""
        subzone = self.subzoneRegistry.getSubzone(subzoneCode)
        origin = profile.anchorCoordinates
        mode = profile.preferredCommuteMode
        commute = self.commuteControl.retrieveCommute(
            origin,
            subzone.centroid,
            mode,
            nextWeekdayPeak(),
            subzoneCode,
        )
        return self.scoringStrategy.computeSuitabilityScore(subzone, profile, commute)

    def generateRankedRecommendations(self, profile: PreferenceProfile) -> RecommendationSet:
        """Generate sorted recommendations for a profile.

        Every subzone remains in the scoring cohort. Public transport near the
        CBD uses the precomputed matrix (with an estimated fallback for missing
        entries); driving/walking and custom workplaces use live OneMap routing.
        Subzones without a commute estimate are scored with that criterion
        treated as missing and reweighted.
        """
        from app.entity.recommendation_set import RecommendationSet

        subzones = self.subzoneRegistry.getAllSubzones()
        origin = profile.anchorCoordinates or Coordinates(CBD_LATITUDE, CBD_LONGITUDE)
        mode = profile.preferredCommuteMode
        commute_result = self.commuteControl.retrieveCommutesSync(
            origin,
            subzones,
            mode,
            nextWeekdayPeak(),
            topK=50,
        )
        warnings = list(commute_result.warnings)
        # Keep every subzone in the cohort. Missing commute estimates are
        # handled by the scoring strategy as a missing criterion and reweighted,
        # rather than silently dropping the subzone from the ranking.
        candidates = subzones
        items = self.scoringStrategy.scoreCandidates(
            candidates,
            profile,
            commute_result.data,
            warnings,
        )
        result = RecommendationSet(
            profileId=profile.getProfileId(),
            generatedTime=datetime.now(timezone.utc),
            dataSnapshotId=self.dataSnapshotId,
            dataAsOf=self.dataAsOf,
            items=items,
            warnings=warnings,
            profileSnapshot=toJsonable(profile),
        )
        result.sortByRank()
        return result
