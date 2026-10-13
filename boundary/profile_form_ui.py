from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.entity.types import ProfileDTO


class ProfileFormUI:
    """«boundary»"""

    currentProfileData: ProfileDTO
    criteriaSliders: dict[str, float]

    def renderForm(self) -> None:
        raise NotImplementedError  # TODO

    def submitProfileData(self) -> None:
        raise NotImplementedError  # TODO

    def displayValidationError(self, message: str) -> None:
        raise NotImplementedError  # TODO
