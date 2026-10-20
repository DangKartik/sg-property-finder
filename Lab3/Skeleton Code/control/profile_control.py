from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from container.profile_catalog import ProfileCatalog
    from entity.types import ProfileForm


class ProfileControl:
    """«control» Creates and updates preference profiles after validating the input."""

    profileCatalog: ProfileCatalog  # private

    def __init__(self, profileCatalog: ProfileCatalog) -> None:
        """Create a ProfileControl with its attributes (TODO: add validation if needed)."""
        self.profileCatalog = profileCatalog

    def createProfile(self, profileData: ProfileForm) -> bool:
        """Create profile (public).

        Args:
            profileData: ProfileForm
        Returns:
            bool
        """
        raise NotImplementedError  # TODO

    def updateProfile(self, id: str, profileData: ProfileForm) -> bool:
        """Update profile (public).

        Args:
            id: str
            profileData: ProfileForm
        Returns:
            bool
        """
        raise NotImplementedError  # TODO
