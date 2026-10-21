"""Criterion weight module."""

from __future__ import annotations
from dataclasses import dataclass

@dataclass
class CriterionWeight:
    """Stereotype: Entity. Entity representing the importance a user assigns to one criterion."""
    criterionId: str
    weightValue: float

    def getCriterionId(self) -> str:
        """Return criterion id.

        Args:
            None.

        Returns:
            str.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def getWeightValue(self) -> float:
        """Return weight value.

        Args:
            None.

        Returns:
            float.

        Failure handling:
            Not applicable at the skeleton level."""
        ...

    def setWeightValue(self, value: float) -> None:
        """Set weight value.

        Args:
            value: float

        Returns:
            None.

        Failure handling:
            Not applicable at the skeleton level."""
        ...
