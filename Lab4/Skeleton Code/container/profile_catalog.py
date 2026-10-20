from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entity.preference_profile import PreferenceProfile


class ProfileCatalog:
    """«container» Holds all saved preference profiles and persists them in the browser's IndexedDB."""

    profiles: dict[str, PreferenceProfile]  # private

    def __init__(self, profiles: dict[str, PreferenceProfile]) -> None:
        """Create a ProfileCatalog with its attributes (TODO: add validation if needed)."""
        self.profiles = profiles

    def addProfile(self, profile: PreferenceProfile) -> None:
        """Add profile (public).

        Args:
            profile: PreferenceProfile
        """
        raise NotImplementedError  # TODO

    def getProfile(self, id: str) -> PreferenceProfile:
        """Get profile (public).

        Args:
            id: str
        Returns:
            PreferenceProfile
        """
        raise NotImplementedError  # TODO

    def getAllProfiles(self) -> list[PreferenceProfile]:
        """Get all profiles (public).

        Returns:
            list[PreferenceProfile]
        """
        raise NotImplementedError  # TODO

    def deleteProfile(self, id: str) -> None:
        """Delete profile (public).

        Args:
            id: str
        """
        raise NotImplementedError  # TODO

    def saveToIndexedDB(self) -> None:
        """Save to indexed db (public)."""
        raise NotImplementedError  # TODO

    def loadFromIndexedDB(self) -> None:
        """Load from indexed db (public)."""
        raise NotImplementedError  # TODO
