from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CriterionDirection(str, Enum):
    MINIMIZE = "MINIMIZE"
    MAXIMIZE = "MAXIMIZE"


@dataclass(frozen=True)
class CriterionDefinition:
    criterionId: str
    criterionName: str
    unit: str
    direction: CriterionDirection
    bufferM: int | None = None
    defaultWeight: float | None = None


class CriterionCatalog:
    definitions: dict[str, CriterionDefinition]

    def __init__(self, definitions: dict[str, CriterionDefinition]) -> None: ...
    def getCriterion(self, criterionId: str) -> CriterionDefinition | None: ...
    def getAllCriteria(self) -> list[CriterionDefinition]: ...
