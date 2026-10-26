"""Recommendation ranking control."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.core.serialization import toJsonable
from app.core.time import CBD_LATITUDE, CBD_LONGITUDE, nextWeekdayPeak
from app.entity.types import Coordinates

if TYPE_CHECKING:
    from app.container.subzone_registry import SubzoneRegistry
    from app.control.commute_control import CommuteControl
    from app.control.data_availability_notifier import DataAvailabilityNotifier
    from app.entity.preference_profile import PreferenceProfile
    from app.entity.recommendation_set import RecommendationSet
    from app.entity.subzone import Subzone
    from app.strategy.scoring_strategy import ScoringStrategy


MAX_RECOMMENDATION_ITEMS = 20


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

    def _rankableSubzones(self) -> list["Subzone"]:
        """Return subzones that have enough source data to rank."""
        return [
            subzone
            for subzone in self.subzoneRegistry.getAllSubzones()
            if subzone.dataAvailable
        ]

    def generateRankedRecommendations(
        self,
        profile: PreferenceProfile,
        limit: int | None = MAX_RECOMMENDATION_ITEMS,
    ) -> RecommendationSet:
        """Generate sorted recommendations for a profile.

        Only subzones marked `dataAvailable` enter the scoring cohort. Public
        transport near the CBD uses the precomputed matrix; driving/walking and
        custom workplaces use live OneMap routing. Subzones without a commute
        estimate from the live/heuristic path are scored with that criterion
        treated as missing and reweighted.

        Args:
            profile: Preference profile to rank.
            limit: Maximum number of returned items. Defaults to the top 20;
                pass `None` for the full ranking (used by comparison).
        """
        from app.entity.recommendation_set import RecommendationSet

        subzones = self._rankableSubzones()
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
        all_items = self.scoringStrategy.scoreCandidates(
            candidates,
            profile,
            commute_result.data,
            warnings,
        )
        items = all_items if limit is None else all_items[: max(0, limit)]
        retained_codes = {item.subzoneId for item in items}
        warnings = [
            warning
            for warning in warnings
            if warning.subzoneCode is None or warning.subzoneCode in retained_codes
        ]
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
