from __future__ import annotations

from typing import TYPE_CHECKING

from app.control.retrieval_control import RetrievalControl

if TYPE_CHECKING:
    from app.entity.environment_info import EnvironmentInfo
    from app.entity.types import RawResponse, RetrievalResult


class EnvironmentRetrievalControl(RetrievalControl):
    def retrieveEnvironmentInfo(self, subzoneCode: str) -> RetrievalResult[EnvironmentInfo]: ...
    def fetchData(self, resourceId: str) -> RawResponse: ...
    def parseResponse(self, data: RawResponse) -> EnvironmentInfo: ...
