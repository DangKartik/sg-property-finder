from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.entity.types import ProfileDTO
    from sgpropfinder.entity.types import ValidationResult


class InputValidationControl:
    """«control»"""

    def validateProfileData(self, data: ProfileDTO) -> ValidationResult:
        raise NotImplementedError  # TODO
