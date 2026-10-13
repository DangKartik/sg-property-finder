from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.control.input_validation_control import InputValidationControl
    from sgpropfinder.container.profile_catalog import ProfileCatalog
    from sgpropfinder.entity.types import ProfileDTO


class ProfileControl:
    """«control»"""

    profileCatalog: ProfileCatalog
    validator: InputValidationControl

    def createProfile(self, data: ProfileDTO) -> str:
        raise NotImplementedError  # TODO

    def updateProfile(self, profileId: str, data: ProfileDTO) -> bool:
        raise NotImplementedError  # TODO

    def deleteProfile(self, profileId: str) -> bool:
        raise NotImplementedError  # TODO
