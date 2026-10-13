from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class CriterionWeight:
    """«entity»"""

    criterionName: str
    weightValue: float

    def getCriterionName(self) -> str:
        raise NotImplementedError  # TODO

    def getWeightValue(self) -> float:
        raise NotImplementedError  # TODO

    def setWeightValue(self, value: float) -> None:
        raise NotImplementedError  # TODO
