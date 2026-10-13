from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.entity.preference_profile import PreferenceProfile


class ProfileSelectorUI:
    """«boundary»"""

    profileDropdownList: list[str]

    def renderDropdown(self, profiles: list[PreferenceProfile]) -> None:
        raise NotImplementedError  # TODO

    def onProfileSelected(self, profileId: str) -> None:
        raise NotImplementedError  # TODO
