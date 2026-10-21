from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CriterionWeight:
    criterionId: str
    weightValue: float

    def getCriterionId(self) -> str: ...
    def getWeightValue(self) -> float: ...
    def setWeightValue(self, value: float) -> None: ...
