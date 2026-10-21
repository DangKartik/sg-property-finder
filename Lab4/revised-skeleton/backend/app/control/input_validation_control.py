from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.entity.types import ValidationResult
    from app.schemas.profile_dto import ProfileDTO


class InputValidationControl:
    def validateProfileData(self, data: ProfileDTO) -> ValidationResult: ...
