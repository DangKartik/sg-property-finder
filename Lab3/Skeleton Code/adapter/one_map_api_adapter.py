from __future__ import annotations


class OneMapApiAdapter:
    """«adapter» Adapter hiding the OneMap API behind a simple interface."""

    baseUrl: str  # private

    def __init__(self, baseUrl: str) -> None:
        """Create a OneMapApiAdapter with its attributes (TODO: add validation if needed)."""
        self.baseUrl = baseUrl

    def fetchDataset(self, datasetId: str) -> str:
        """Fetch dataset (public).

        Args:
            datasetId: str
        Returns:
            str
        Note: Diagram puts fetchDataset on the OneMap adapter (it reads like a data.gov.sg call).
        """
        raise NotImplementedError  # TODO
