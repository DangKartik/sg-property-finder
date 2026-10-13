from __future__ import annotations

from sgpropfinder.control.retrieval_control import RetrievalControl
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.entity.environment_info import EnvironmentInfo
    from sgpropfinder.entity.types import RawResponse


class EnvironmentRetrievalControl(RetrievalControl):
    """«control»"""

    def retrieveEnvironmentInfo(self, subzoneCode: str) -> EnvironmentInfo:
        raise NotImplementedError  # TODO

    def parseResponse(self, data: RawResponse) -> EnvironmentInfo:
        raise NotImplementedError  # TODO
