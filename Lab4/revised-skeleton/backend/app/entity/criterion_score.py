"""Criterion score module."""

from __future__ import annotations
from dataclasses import dataclass

@dataclass
class CriterionScore:
    """Stereotype: Entity. Entity value object explaining one criterion's contribution to a suitability score."""
    criterionId: str
    rawValue: float
    normalisedScore: float
    weight: float
    weightedScore: float
    isMissing: bool
    source: str

    def getCriterionId(self) -> str:
        """Return criterion id.

        Args:
            None.

        Returns:
            str.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getRawValue(self) -> float:
        """Return raw value.

        Args:
            None.

        Returns:
            float.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getNormalisedScore(self) -> float:
        """Return normalised score.

        Args:
            None.

        Returns:
            float.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getWeight(self) -> float:
        """Return weight.

        Args:
            None.

        Returns:
            float.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getWeightedScore(self) -> float:
        """Return weighted score.

        Args:
            None.

        Returns:
            float.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getIsMissing(self) -> bool:
        """Return is missing.

        Args:
            None.

        Returns:
            bool.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getSource(self) -> str:
        """Return source.

        Args:
            None.

        Returns:
            str.

        Failure handling:
            Not applicable at the skeleton level."""
        ...
