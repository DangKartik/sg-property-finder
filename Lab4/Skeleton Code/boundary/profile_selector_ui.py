from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from control.ranking_control import RankingControl
    from entity.preference_profile import PreferenceProfile


class ProfileSelectorUI:
    """«boundary» Dropdown of saved preference profiles; selecting one triggers ranking."""

    rankingControl: RankingControl  # private

    def __init__(self, rankingControl: RankingControl) -> None:
        """Create a ProfileSelectorUI with its attributes (TODO: add validation if needed)."""
        self.rankingControl = rankingControl

    def renderSelector(self, profiles: list[PreferenceProfile]) -> None:
        """Render selector (public).

        Args:
            profiles: list[PreferenceProfile]
        """
        raise NotImplementedError  # TODO

    def onSelectProfile(self, profileId: str) -> None:
        """On select profile (public).

        Args:
            profileId: str
        """
        raise NotImplementedError  # TODO
