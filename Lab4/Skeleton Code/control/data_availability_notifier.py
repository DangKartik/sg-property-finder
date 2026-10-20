from __future__ import annotations


class DataAvailabilityNotifier:
    """«control» Tells the user when data for a subzone or criterion is unavailable."""

    def notifyMissingData(self, source: str, entityId: str) -> None:
        """Notify missing data (public).

        Args:
            source: str
            entityId: str
        """
        raise NotImplementedError  # TODO
