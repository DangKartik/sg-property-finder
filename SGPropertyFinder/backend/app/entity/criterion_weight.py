"""Criterion weight entity."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CriterionWeight:
    """Stereotype: Entity. A 1–10 importance rating for one criterion."""

    criterionId: str
    weightValue: float

    def getCriterionId(self) -> str:
        """Return the criterion identifier."""
        return self.criterionId

    def getWeightValue(self) -> float:
        """Return the assigned weight."""
        return self.weightValue

    def setWeightValue(self, value: float) -> None:
        """Set the assigned weight."""
        self.weightValue = float(value)
