from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class EnvironmentInfo:
    """«entity»"""

    weatherPattern: str
    greenCoveragePercent: float

    def getWeatherPattern(self) -> str:
        raise NotImplementedError  # TODO

    def getGreenCoveragePercent(self) -> float:
        raise NotImplementedError  # TODO
