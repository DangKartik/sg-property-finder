from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.control.neighborhood_details_control import NeighborhoodDetailsControl
    from app.control.ranking_control import RankingControl
    from app.entity.comparison_result import ComparisonResult
    from app.entity.preference_profile import PreferenceProfile


class ComparisonControl:
    rankingControl: RankingControl
    detailsControl: NeighborhoodDetailsControl

    def __init__(
        self,
        rankingControl: RankingControl,
        detailsControl: NeighborhoodDetailsControl,
    ) -> None: ...
    def compare(
        self,
        profile: PreferenceProfile,
        subzoneCodes: list[str],
    ) -> ComparisonResult: ...
