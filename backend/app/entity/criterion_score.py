"""Criterion score entity."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CriterionScore:
    """Stereotype: Entity. One criterion's contribution to a suitability score."""

    criterionId: str
    rawValue: float
    normalisedScore: float
    weight: float
    weightedScore: float
    isMissing: bool
    source: str

    def getCriterionId(self) -> str:
        """Return the criterion identifier."""
        return self.criterionId

    def getRawValue(self) -> float:
        """Return the raw metric value."""
        return self.rawValue

    def getNormalisedScore(self) -> float:
        """Return the 0-1 normalised score."""
        return self.normalisedScore

    def getWeight(self) -> float:
        """Return the renormalised weight."""
        return self.weight

    def getWeightedScore(self) -> float:
        """Return normalisedScore * weight."""
        return self.weightedScore

    def getIsMissing(self) -> bool:
        """Return whether the criterion was missing."""
        return self.isMissing

    def getSource(self) -> str:
        """Return the source label."""
        return self.source
