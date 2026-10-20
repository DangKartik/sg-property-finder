from __future__ import annotations


class NotificationModalUI:
    """«boundary» Shows notifications and error messages to the user in a modal."""

    currentMessage: str  # private

    def __init__(self, currentMessage: str) -> None:
        """Create a NotificationModalUI with its attributes (TODO: add validation if needed)."""
        self.currentMessage = currentMessage

    def showNotification(self, message: str, type: str) -> None:
        """Show notification (public).

        Args:
            message: str
            type: str
        """
        raise NotImplementedError  # TODO

    def dismiss(self) -> None:
        """Dismiss (public)."""
        raise NotImplementedError  # TODO
