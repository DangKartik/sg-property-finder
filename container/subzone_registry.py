from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.entity.subzone import Subzone


class SubzoneRegistry:
    """«container»"""

    subzones: dict[str, Subzone]

    def registerSubzone(self, subzone: Subzone) -> None:
        raise NotImplementedError  # TODO

    def getSubzone(self, subzoneCode: str) -> Subzone:
        raise NotImplementedError  # TODO

    def getAllSubzones(self) -> list[Subzone]:
        raise NotImplementedError  # TODO
