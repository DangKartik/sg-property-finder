"""Side-by-side comparison control."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.entity.comparison_result import ComparisonResult

if TYPE_CHECKING:
    from app.control.neighborhood_details_control import NeighborhoodDetailsControl
    from app.control.ranking_control import RankingControl
    from app.entity.preference_profile import PreferenceProfile


class ComparisonControl:
    """Stereotype: Control. Builds comparison results for selected subzones."""

    def __init__(
        self,
        rankingControl: RankingControl,
        detailsControl: NeighborhoodDetailsControl,
    ) -> None:
        """Store ranking and factsheet dependencies."""
        self.rankingControl = rankingControl
        self.detailsControl = detailsControl

    def compare(
        self,
        profile: PreferenceProfile,
        subzoneCodes: list[str],
    ) -> ComparisonResult:
        """Return score items and full factsheets for two or more subzones.

        Raises:
            ValueError: If fewer than two unique subzone codes are supplied.
        """
        unique_codes = list(dict.fromkeys(subzoneCodes))
        if len(unique_codes) < 2:
            raise ValueError("Select at least two subzones to compare")
        if len(unique_codes) > 4:
            raise ValueError("Compare at most four subzones at a time")
        recommendations = self.rankingControl.generateRankedRecommendations(
            profile, limit=None
        )
        selected = [item for item in recommendations.getItems() if item.subzoneId in unique_codes]
        details = [self.detailsControl.fetchNeighborhoodDetails(code, profile) for code in unique_codes]
        best = max(selected, key=lambda item: item.totalScore) if selected else None
        return ComparisonResult(
            profileId=profile.getProfileId(),
            generatedTime=datetime.now(timezone.utc),
            items=selected,
            details=details,
            bestSubzoneId=best.subzoneId if best else None,
            summary=(
                f"Compared {len(unique_codes)} subzones; best score: "
                f"{best.subzoneName if best else 'n/a'}"
            ),
        )
