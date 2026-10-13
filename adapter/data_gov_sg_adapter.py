from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class DataGovSgAdapter:
    """«adapter»"""

    apiEndpoint: str

    def fetchDataset(self, resourceId: str) -> dict:
        raise NotImplementedError  # TODO
