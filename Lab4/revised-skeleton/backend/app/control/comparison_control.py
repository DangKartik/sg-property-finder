"""Comparison control module."""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.control.neighborhood_details_control import NeighborhoodDetailsControl
    from app.control.ranking_control import RankingControl
    from app.entity.comparison_result import ComparisonResult
    from app.entity.preference_profile import PreferenceProfile

class ComparisonControl:
    """Stereotype: Control. Control that builds side-by-side comparison results for selected subzones."""
    rankingControl: RankingControl
    detailsControl: NeighborhoodDetailsControl

    def __init__(self, rankingControl: RankingControl, detailsControl: NeighborhoodDetailsControl) -> None:
        """Initialise the ComparisonControl with its dependencies.

        Args:
            rankingControl: RankingControl
            detailsControl: NeighborhoodDetailsControl

        Returns:
            None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def compare(self, profile: PreferenceProfile, subzoneCodes: list[str]) -> ComparisonResult:
        """Build a comparison result with full details for the selected subzones.

        Args:
            profile: PreferenceProfile
            subzoneCodes: list[str]

        Returns:
            ComparisonResult.

        Failure handling:
            Not applicable at the skeleton level."""
        ...
