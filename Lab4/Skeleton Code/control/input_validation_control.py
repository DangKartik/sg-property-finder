from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entity.types import ValidationResult


class InputValidationControl:
    """«control» Validates profile form input and reports errors."""

    def validateProfileForm(self, formData: dict[str, object]) -> ValidationResult:
        """Validate profile form (public).

        Args:
            formData: dict[str, object]
        Returns:
            ValidationResult
        """
        raise NotImplementedError  # TODO
