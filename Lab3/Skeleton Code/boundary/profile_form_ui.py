from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from control.profile_control import ProfileControl


class ProfileFormUI:
    """«boundary» Form where the user keys in a preference profile and criterion weights."""

    profileControl: ProfileControl  # private

    def __init__(self, profileControl: ProfileControl) -> None:
        """Create a ProfileFormUI with its attributes (TODO: add validation if needed)."""
        self.profileControl = profileControl

    def renderForm(self) -> None:
        """Render form (public)."""
        raise NotImplementedError  # TODO

    def onSubmit(self, formData: dict[str, object]) -> None:
        """On submit (public).

        Args:
            formData: dict[str, object]
        """
        raise NotImplementedError  # TODO
