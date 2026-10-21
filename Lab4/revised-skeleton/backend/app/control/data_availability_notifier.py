from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.entity.types import DataAvailabilityCode
    from app.schemas.data_availability_warning import DataAvailabilityWarning


class DataAvailabilityNotifier:
    def notifyDataUnavailable(
        self,
        datasetCode: str,
        subzoneCode: str | None = None,
        code: DataAvailabilityCode | None = None,
        source: str = "data.gov.sg",
        isStale: bool = False,
        isRetryable: bool = False,
    ) -> DataAvailabilityWarning: ...
