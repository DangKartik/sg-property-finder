from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.entity.subzone import Subzone


class SubzoneRegistry:
    subzones: dict[str, Subzone]

    def __init__(self, subzones: dict[str, Subzone]) -> None: ...
    def registerSubzone(self, subzone: Subzone) -> None: ...
    def getSubzone(self, subzoneCode: str) -> Subzone: ...
    def getAllSubzones(self) -> list[Subzone]: ...
