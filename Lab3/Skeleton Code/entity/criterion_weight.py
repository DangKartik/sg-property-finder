from __future__ import annotations


class CriterionWeight:
    """«entity» The importance a user assigns to one criterion."""

    criterionName: str  # private
    weightValue: float  # private

    def __init__(self, criterionName: str, weightValue: float) -> None:
        """Create a CriterionWeight with its attributes (TODO: add validation if needed)."""
        self.criterionName = criterionName
        self.weightValue = weightValue

    def getCriterionName(self) -> str:
        """Get criterion name (public).

        Returns:
            str
        """
        raise NotImplementedError  # TODO

    def getWeightValue(self) -> float:
        """Get weight value (public).

        Returns:
            float
        """
        raise NotImplementedError  # TODO
