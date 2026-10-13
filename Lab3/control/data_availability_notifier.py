from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sgpropfinder.boundary.notification_modal_ui import NotificationModalUI


class DataAvailabilityNotifier:
    """«control»"""

    notificationUI: NotificationModalUI

    def notifyDataUnavailable(self, datasetName: str) -> None:
        raise NotImplementedError  # TODO
