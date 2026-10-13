from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.entity.preference_profile import PreferenceProfile


class ProfileCatalog:
    """«container»"""

    profiles: dict[str, PreferenceProfile]

    def addProfile(self, profile: PreferenceProfile) -> None:
        raise NotImplementedError  # TODO

    def getProfile(self, profileId: str) -> PreferenceProfile:
        raise NotImplementedError  # TODO

    def getAllProfiles(self) -> list[PreferenceProfile]:
        raise NotImplementedError  # TODO

    def removeProfile(self, profileId: str) -> bool:
        raise NotImplementedError  # TODO

    def saveToLocalStorage(self) -> None:
        raise NotImplementedError  # TODO

    def loadFromLocalStorage(self) -> None:
        raise NotImplementedError  # TODO
