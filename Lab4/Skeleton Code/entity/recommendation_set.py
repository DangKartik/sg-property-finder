from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from entity.recommendation_item import RecommendationItem


class RecommendationSet:
    """«entity» The set of ranked recommendations generated for a profile."""

    setId: str  # private
    generatedTimestamp: datetime  # private
    items: list[RecommendationItem]  # private

    def __init__(self, setId: str, generatedTimestamp: datetime, items: list[RecommendationItem]) -> None:
        """Create a RecommendationSet with its attributes (TODO: add validation if needed)."""
        self.setId = setId
        self.generatedTimestamp = generatedTimestamp
        self.items = items

    def addItem(self, item: RecommendationItem) -> None:
        """Add item (public).

        Args:
            item: RecommendationItem
        """
        raise NotImplementedError  # TODO

    def getSortedItems(self) -> list[RecommendationItem]:
        """Get sorted items (public).

        Returns:
            list[RecommendationItem]
        """
        raise NotImplementedError  # TODO
