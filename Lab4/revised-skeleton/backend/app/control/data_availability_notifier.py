"""Data availability notifier module."""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.entity.data_availability_warning import DataAvailabilityWarning
    from app.entity.enums import DataAvailabilityCode

class DataAvailabilityNotifier:
    """Stereotype: Control. Stateless control that creates data-availability warnings for one request."""

    def notifyDataUnavailable(self, datasetCode: str, subzoneCode: str | None=None, code: DataAvailabilityCode | None=None, source: str='data.gov.sg', isStale: bool=False, isRetryable: bool=False) -> DataAvailabilityWarning:
        """Build a warning for one dataset without retaining shared state.

        Args:
            datasetCode: str
            subzoneCode: str | None
            code: DataAvailabilityCode | None
            source: str
            isStale: bool
            isRetryable: bool

        Returns:
            DataAvailabilityWarning.

        Failure handling:
            Not applicable at the skeleton level."""
        ...
